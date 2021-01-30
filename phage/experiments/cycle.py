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


class Replication(Process):
    defaults = {}

    def ports_schema(self):
        return {
            'genes': {
                '*': {
                    'state': 'active',
                    'number': 1,
                }
            }
        }

    def next_update(self, timestep, states):
        return {}


class Cell(Composite):
    defaults = {
        'growth': {},
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
    initial_state = {}
    experiment_settings = {
        'initial_state': initial_state}
    cycle_experiment = compose_experiment(
        hierarchy=hierarchy,
        settings=experiment_settings)

    import ipdb; ipdb.set_trace()

    cycle_experiment.update(4800.0)

    plot_agents_multigen(cycle_experiment.emitter.get_data(), out_dir='plots')

if __name__ == '__main__':
    run_cycle()
