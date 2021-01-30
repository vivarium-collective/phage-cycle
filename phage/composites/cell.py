import numpy as np
from vivarium import DivideCondition, MetaDivision
from vivarium.core.process import Process, Composite


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
    defaults = {}

    def ports_schema(self):
        return {
            'genes': {
                '*': {
                    'activation': {'_default': 0.0},
                    'copy_number': {'_default': 1},
                }
            }
        }

    def next_update(self, timestep, states):
        return {}


class Cell(Composite):
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
            generator=self)

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
                'genes': ('genes',),
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