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

# helper functions for composition
from vivarium.core.composition import composite_in_experiment
from vivarium.core.emitter import remove_units, deserialize_value
from vivarium.processes.timeline import TimelineProcess

# composites
from phage_cycle.composites.cell import Cell
from phage_cycle.composites.phage import Phage

# plots
from vivarium.plots.agents_multigen import plot_agents_multigen


def test_cycle():

    cell_id = 'cell_0'
    phage_id = 'phage_0'

    cell_composer = Cell({
        'agent_id': cell_id,
        'agents_path': ('..', '..', 'cells',),
        'growth': {
            'growth_rate': 1e-4
        }
    })

    phage_composer = Phage({
        'agent_id': phage_id,
        'cells_path': ('..', '..', 'cells',),})

    timeline_config = {
        'timeline': [
            (10, {('phages', phage_id, 'attach'): cell_id})]
    }

    # TODO -- replace timeline with a "neighbors" process where
    #   each phage stochastically attaches to a cell.
    timeline_process = TimelineProcess(timeline_config)
    timeline_composite = timeline_process.generate()

    cell_composite = cell_composer.generate(path=('cells', cell_id))
    phage_composite = phage_composer.generate(path=('phages', phage_id))
    cell_composite.merge(composite=phage_composite)
    cell_composite.merge(composite=timeline_composite)

    initial_state = cell_composite.initial_state()

    settings = {}
    exp = composite_in_experiment(cell_composite, settings, initial_state=initial_state)

    exp.update(30)

    timeseries = exp.emitter.get_timeseries()
    data = exp.emitter.get_data()
    data = deserialize_value(data)
    data = remove_units(data)

    # plot
    settings = {
        'agents_key': 'cells'
    }
    plot_agents_multigen(
        data,
        settings=settings,
        out_dir='out',
        filename='phage_cycle')


    import ipdb; ipdb.set_trace()


if __name__ == '__main__':
    test_cycle()
