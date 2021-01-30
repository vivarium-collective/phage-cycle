"""

Outline of events:
1. lysogenic cycle / gene replication
    * DNA replication (without forks)
    * standard cell growth expression program
    * cell division

2. phage attachment / gene insertion / gene integration
    * phage finds/attaches cell in an environment
    * inject DNA into cell. dictionary merge with cell's DNA

3. trigger/activation
    * clock process (start with a timer state?)
        * alternative processes?

4. phage expression
    * phage protein expressed
    * phage DNA replicated

5. phage assembly
    * DNA goes into the protein capsule to produce a complete phage compartment

6. lysis
    * accumulation of phage triggers a bursting process. threshold process detects condition and sets trigger to true


Tree structure, with *=compartment, -=variable:
    * environment
        * Cell
            * DNA
                - replication gene
                - phage gene? latent
            - Protein capsule
            - biomass
            * Phage
        * Phage
            * DNA
                - phage gene

required variables:
    * gene sequence -- dictionary with {name: state (repressed, active, etc)}
        * one gene for replication
        * one gene for phage
    * biomass units? use mass conservation.


required processes:
    *
"""

from vivarium.core.process import (
    Process,
    Deriver,
    Composite)

# helper functions for composition
from vivarium.core.composition import (
    compose_experiment,
    FACTORY_KEY,
)

from vivarium.processes.meta_division import MetaDivision
from vivarium.processes.divide_condition import DivideCondition
from vivarium.processes.burst import Burst

from vivarium.plots.agents_multigen import plot_agents_multigen

import numpy as np

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
        total_biomass = states['biomass'] * np.exp(self.parameters['growth_rate'] * timestep)

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



def run_cycle():
    cell_id = 'cell_1'
    phage_id = 'phage_1'
    environment_config = {}
    cell_config = {
        'agent_id': cell_id
    }
    phage_config = {}

    # declare the hierarchy
    hierarchy = {
        # FACTORY_KEY: {
        #     'type': Environment,
        #     'config': environment_config},
        'agents': {
            cell_id: {
                FACTORY_KEY: {
                    'type': Cell,
                    'config': cell_config}
            },
            # phage_id: {
            #     FACTORY_KEY: {
            #         'type': Phage,
            #         'config': phage_config}
            # },
        }
    }

    # configure experiment
    initial_state = {
        'agents': {
            cell_id: {
                'genes': {
                    'A': {
                        'copy_number': 1.0,
                        'activation': 1e-3,
                    }
                },
                'proteins': {
                    'A': {
                        'mw': 1e-1
                    }
                },
            }
        }
    }
    experiment_settings = {
        'initial_state': initial_state}
    cycle_experiment = compose_experiment(
        hierarchy=hierarchy,
        settings=experiment_settings)

    cycle_experiment.update(4800.0)

    plot_agents_multigen(cycle_experiment.emitter.get_data(), out_dir='out')

if __name__ == '__main__':
    run_cycle()
