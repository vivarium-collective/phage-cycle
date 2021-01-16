"""

Outline of events:
1. lysogenic cycle / gene replication
    * DNA replication (without forks)
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

# helper functions for composition
from vivarium.core.composition import (
    compose_experiment,
    FACTORY_KEY,
)


def Cell



def run_cycle():
    cell_id = 'cell_1'
    phage_id = 'phage_1'
    environment_config = {}
    cell_config = {}
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


if __name__ == '__main__':
    run_cycle()
