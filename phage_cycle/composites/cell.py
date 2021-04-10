import numpy as np

from vivarium import DivideCondition, MetaDivision
from vivarium.core.process import Process, Composer, Deriver
from vivarium.library.units import units

from scipy.constants import N_A
avogadro = N_A # / units.mol

from vivarium.core.composition import composer_in_experiment


class TotalBiomass(Deriver):
    defaults = {
        'metabolite_mass': 1.0 * units.fg,
        'gene_mass': 1.0 * units.fg,
    }

    def __init__(self, parameters=None):
        super().__init__(parameters)

    def ports_schema(self):
        return {
            'biomass': {
                '_default': 0 * units.fg,
                '_updater': 'set',
            },
            'metabolites': {},
            'incomplete_replication': {},
            'genes': {
                '*': {
                    'copy_number': {},
                    'length': {},
                }
            },
            'proteins': {
                '*': {
                    'count': {},
                    'mw': {},
                }
            },
        }

    def next_update(self, timestep, state):
        metabolites = state['metabolites']
        genes = state['genes']
        incomplete_replication = state['incomplete_replication']
        proteins = state['proteins']

        mass = metabolites * self.parameters['metabolite_mass']
        mass += incomplete_replication * self.parameters['gene_mass']
        for protein in proteins.values():
            mass += protein['count'] * protein['mw'] / avogadro
        for gene in genes.values():
            mass += gene['copy_number'] * gene['length'] * self.parameters['gene_mass']

        return {
            'biomass': mass
        }


class Growth(Process):
    defaults = {
        'growth_rate': 5e-4,
    }

    def __init__(self, parameters=None):
        super().__init__(parameters)

    def ports_schema(self):
        return {
            'metabolites': {
                '_default': 1.0,
                '_emit': True,
                '_divider': 'split',
            },
            'biomass': {
                '_default': 1.0 * units.fg,
                '_emit': True,
                '_divider': 'split',
            }
        }

    def initial_state(self, config):
        return {
            'metabolites': 10.0,
        }

    def next_update(self, timestep, states):
        metabolites = states['metabolites']
        biomass = states['biomass']
        total_metabolites = biomass.to('fg').magnitude * np.exp(
            self.parameters['growth_rate'] * timestep)
        delta_metabolites = total_metabolites - metabolites
        return {
            'metabolites': delta_metabolites
        }


class Expression(Process):
    defaults = {
        'expression_rate': 1e-1,
        'metabolite_mass': 1.0 * units.fg,
        'genes': {
            'growth': {
                'initial_activation': 1.0,
                'initial_copy_number': 1,
                'length': 20.0,
            }
        },
        'proteins': {
            'growth': {
                'initial_count': 10,
                'metabolite_cost': 1.0,
                'mw': 1.0 * units.fg,
            }
        }
    }

    def ports_schema(self):
        return {
            'metabolites': {},
            'genes': {
                '*': {
                    'activation': {'_default': 0.0},
                    'copy_number': {
                        '_default': 1,
                        '_emit': True,
                    },
                    'length': {'_default': 0},
                }
            },
            'proteins': {
                '*': {
                    'count': {
                        '_default': 0,
                        '_divider': 'split',
                        '_emit': True,
                    },
                    'metabolite_cost': {'_default': 1.0},
                    'mw': {'_default': 1.0 * units.fg},
                }
            }
        }

    def initial_state(self, config):
        genes = {
            gene: {
                'activation': spec['initial_activation'],
                'copy_number': spec['initial_copy_number'],
                'length': spec['length'],
            }
            for gene, spec in self.parameters['genes'].items()
        }

        proteins = {
            protein: {
                'count': spec['initial_count'],
                'metabolite_cost': spec['metabolite_cost'],
                'mw': spec['mw'],
            }
            for protein, spec in self.parameters['proteins'].items()
        }

        return {
            'genes': genes,
            'proteins': proteins,
        }

    def next_update(self, timestep, states):
        metabolites = states['metabolites']
        genes = states['genes']
        proteins = states['proteins']

        protein_created = {}
        metabolites_used = 0
        for gene, gene_state in genes.items():
            protein_created[gene] = self.parameters['expression_rate'] * metabolites * timestep * gene_state['activation'] * gene_state['copy_number']
            metabolites_used += protein_created[gene] * proteins[gene]['metabolite_cost']

        update = {
            'metabolites': -metabolites_used,
            'proteins': {
                protein: {
                    'count': count}
                for protein, count in protein_created.items()}}

        return update


class Replication(Process):
    defaults = {
        'elongation_rate': 3,
        'nucleotide_metabolite_cost': 0.01} # base pairs / second

    def ports_schema(self):
        return {
            'incomplete_replication': {
                '_default': 0.0,
                '_updater': 'set',
                '_emit': True,
            },
            'dna_polymerase_position': {
                '_default': 0.0,
                '_emit': True
            },
            'metabolites': {},
            'genes': {
                '*': {
                    'activation': {'_default': 0.0},
                    'copy_number': {
                        '_default': 1,
                        '_divider': 'split'
                    },
                    'length': {'_default': 100.0},
                }
            }
        }

    def initial_state(self, config):
        return {
            'dna_polymerase_position': 0.0,
            'incomplete_replication': 0,
        }

    def next_update(self, timestep, states):
        genes = states['genes']
        position = states['dna_polymerase_position']
        position_delta = self.parameters['elongation_rate'] * timestep
        new_position = position + position_delta
        metabolites_used = position_delta * self.parameters['nucleotide_metabolite_cost']

        update = {
            'metabolites': -metabolites_used,
            'genes': {}
        }

        first_gene = [gene for gene_key, gene in genes.items()][0]

        cursor = 0
        incomplete_replication = new_position * first_gene['copy_number']
        for gene_key, gene in genes.items():
            copy_number = genes[gene_key]['copy_number']
            cursor += gene['length']

            if position < cursor and cursor <= new_position:
                update['genes'][gene_key] = {
                    'copy_number': copy_number
                }
                copy_number += copy_number

            # comes after copy number assignment so that it uses the new copy number to
            # determine how much incomplete replication exists
            if new_position >= cursor:
                incomplete_replication = (new_position - cursor) * copy_number
        
        if new_position >= cursor:
            update['dna_polymerase_position'] = position_delta - cursor
        else:
            update['dna_polymerase_position'] = position_delta

        update['incomplete_replication'] = incomplete_replication

        return update


class Cell(Composer):
    defaults = {
        'growth': {},
        'expression': {},
        'replication': {},
        'divide_condition': {'threshold': 20},
        'daughter_path': tuple(),
        'agents_path': tuple(),
        'metabolite_mass': 1.0 * units.fg,
    }

    def generate_processes(self, config):

        # division config
        daughter_path = config['daughter_path']
        agent_id = config['agent_id']
        division_config = dict(
            config.get('division', {}),
            daughter_path=daughter_path,
            agent_id=agent_id,
            composer=self)

        expression_config = dict(
            config['expression'],
            metabolite_mass=self.config['metabolite_mass']
        )

        biomass_config = {
            'metabolite_mass': self.config['metabolite_mass']
        }

        return {
            'growth': Growth(config['growth']),
            'expression': Expression(expression_config),
            'replication': Replication(config['replication']),
            'total_biomass': TotalBiomass(biomass_config),
            # 'divide_condition': DivideCondition(config['divide_condition']),
            'meta_division': MetaDivision(division_config),
            # 'burst': Burst(),
        }

    def generate_topology(self, config):
        return {
            'growth': {
                'biomass': ('biomass',),
                'metabolites': ('metabolites',),
            },
            'expression': {
                'metabolites': ('metabolites',),
                'genes': ('genes',),
                'proteins': ('proteins',)
            },
            'replication': {
                'metabolites': ('metabolites',),
                'genes': ('genes',),
                'incomplete_replication': ('dna', 'incomplete_replication',),
                'dna_polymerase_position': ('dna', 'polymerase_position')
            },
            'total_biomass': {
                'biomass': ('biomass',),
                'metabolites': ('metabolites',),
                'genes': ('genes',),
                'incomplete_replication': ('dna', 'incomplete_replication',),
                'proteins': ('proteins',),
            },
            # 'divide_condition': {
            #     'variable': ('biomass',),
            #     'divide': ('boundary', 'divide',),
            # },
            'meta_division': {
                'global': ('boundary',),
                'agents': config['agents_path'],
            },
            # 'burst': {}
        }


def test_cell():
    cell_config = {
        'agent_id': '1',
        'agents_path': ('agents',),
        'growth': {'growth_rate': 1e-1},
    }
    cell_composer = Cell(cell_config)
    initial_state = {
        'agents': {
            '1': cell_composer.initial_state()}}

    cell_experiment = composer_in_experiment(
        cell_composer,
        initial_state=initial_state,
        outer_path=('agents', '1'))

    cell_experiment.update(10)

    timeseries = cell_experiment.emitter.get_timeseries()

    import ipdb; ipdb.set_trace()

if __name__ == '__main__':
    test_cell()
