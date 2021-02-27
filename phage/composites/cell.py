import numpy as np
from vivarium import DivideCondition, MetaDivision
from vivarium.core.process import Process, Composer

from vivarium.core.composition import composer_in_experiment


class Growth(Process):
    defaults = {
        'growth_rate': 5e-4}

    def ports_schema(self):
        return {
            'biomass': {
                '_default': 1.0,
                '_emit': True,
                '_divider': 'split',
            }
        }

    def initial_state(self, config):
        return {
            'biomass': 1.0}

    def next_update(self, timestep, states):
        biomass = states['biomass']
        total_biomass = biomass * np.exp(self.parameters['growth_rate'] * timestep)

        return {
            'biomass': total_biomass - states['biomass']}


class Expression(Process):
    defaults = {
        'expression_rate': 1e-1}

    def ports_schema(self):
        return {
            'biomass': {},
            'genes': {
                '*': {
                    'activation': {'_default': 0.0},
                    'copy_number': {
                        '_default': 1,
                        '_emit': True,
                    }}},
            'proteins': {
                '*': {
                    'count': {
                        '_default': 0,
                        '_divider': 'split',
                        '_emit': True,
                    },
                    'mw': {'_default': 1}}}}

    def initial_state(self, config):
        return {
            'genes': {
                'growth': {
                    'activation': 1.0,
                    'copy_number': 1}},
            'proteins': {
                'growth': {
                    'count': 10,
                    'mw': 1.0}}}

    def next_update(self, timestep, states):
        biomass = states['biomass']
        genes = states['genes']
        proteins = states['proteins']

        protein_created = {}
        biomass_used = 0
        for gene, gene_state in genes.items():
            protein_created[gene] = self.parameters['expression_rate'] * biomass * timestep * gene_state['activation'] * gene_state['copy_number']
            biomass_used += protein_created[gene] * proteins[gene]['mw']

        update = {
            'biomass': -biomass_used,
            'proteins': {
                protein: {
                    'count': count}
                for protein, count in protein_created.items()}}
        return update


class Replication(Process):
    defaults = {
        'elongation_rate': 10,
        'nucleotide_mw': 0.01} # base pairs / second

    def ports_schema(self):
        return {
            'biomass': {},
            'dna_polymerase_position': {
                '_default': 0.0},
            'genes': {
                '*': {
                    'activation': {'_default': 0.0},
                    'copy_number': {
                        '_default': 1,
                        '_divider': 'split'},
                    'length': {'_default': 1000.0},
                }
            }
        }

    def initial_state(self, config):
        return {
            'dna_polymerase_position': 0.0}

    def next_update(self, timestep, states):
        position = states['dna_polymerase_position']
        position_delta = self.parameters['elongation_rate'] * timestep
        new_position = position + position_delta
        biomass_used = position_delta * self.parameters['nucleotide_mw']

        update = {
            'biomass': -biomass_used,
            'genes': {}}

        cursor = 0.0
        for gene_key, gene in states['genes'].items():
            cursor += gene['length']
            if position < cursor and cursor <= new_position:
                update['genes'][gene_key] = {}
                update['genes'][gene_key]['copy_number'] = states['genes'][gene_key]['copy_number']
        
        if new_position >= cursor:
            update['dna_polymerase_position'] = position_delta - cursor
        else:
            update['dna_polymerase_position'] = position_delta

        return update


class Cell(Composer):
    defaults = {
        'growth': {},
        'expression': {},
        'replication': {},
        'divide_condition': {
            'threshold': 2},
        'daughter_path': tuple(),
        'agents_path': ('..', '..', 'agents',),
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

        return {
            'growth': Growth(config['growth']),
            'expression': Expression(config['expression']),
            'replication': Replication(config['replication']),
            'divide_condition': DivideCondition(config['divide_condition']),
            'meta_division': MetaDivision(division_config),
            # 'burst': Burst(),
        }

    def generate_topology(self, config):
        return {
            'growth': {
                'biomass': ('biomass',),
            },
            'expression': {
                'biomass': ('biomass',),
                'genes': ('genes',),
                'proteins': ('proteins',)},
            'replication': {
                'biomass': ('biomass',),
                'genes': ('genes',),
                'dna_polymerase_position': ('dna', 'polymerase_position')
            },
            'divide_condition': {
                'variable': ('biomass',),
                'divide': ('boundary', 'divide',),
            },
            'meta_division': {
                'global': ('boundary',),
                'agents': config['agents_path'],
            },
            # 'burst': {}
        }


def test_cell():
    cell_config = {
        'agent_id': '1',
        'agents_path': ('agents',)
    }
    cell_composer = Cell(cell_config)
    initial_state = {
        'agents': {
            '1': cell_composer.initial_state()}}

    cell_experiment = composer_in_experiment(
        cell_composer,
        initial_state=initial_state,
        outer_path=('agents', '1'))

    cell_experiment.update(101)

    import ipdb; ipdb.set_trace()


if __name__ == '__main__':
    test_cell()
