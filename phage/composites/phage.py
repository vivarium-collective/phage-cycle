from vivarium.core.process import Process, Composer
from vivarium.core.composition import composer_in_experiment


class Activation(Process):
    """
    TODO: how many generations are expected before phage proteins appear and assemble?
    """
    defaults = {
        'composer': Phage,
        'threshold': 1
    }

    def __init__(self, parameters=None):
        super().__init__(parameters)
        self.composer = self.parameters['composer']

    def ports_schema(self):
        return {
            'protein': {
                'phage': {},
            }
        }
    def next_update(self, timestep, states):
        # once sufficient phage protein is found, generate a Phage
        if states['protein']['phage']['count'] > self.parameters['threshold']:
            composite = self.composer.generate({})
            return {
                '_generate': {
                    'processes': composite['processes'],
                    'topology': composite['topology'],
                    'initial_state': {}
                }
            }


class AttachInsert(Process):
    """
    This gives the Phage access to a given cell, and generates an Insertion Process inside the cell
    """
    defaults = {
        'composer': Activation
    }

    def __init__(self, parameters=None):
        super().__init__(parameters)
        self.composer = self.parameters['composer']

    def ports_schema(self):
        return {
            'attach': {
                '_default': None},
            'cells': {
                '*': {
                    'genes': {},
                    'proteins': {},
                }
            },
        }

    def next_update(self, timestep, states):
        # receive a cell_id to attach insertion's genes and proteins ports.
        if states['attach']:
            composite = self.composer.generate({})
            return {
                # add genes and proteins to the cell
                'cells': {
                    states['attach']: {
                        '_add': [
                            {'key': 'genes', 'state': 'phage'},
                            {'key': 'proteins', 'state': 'phage'},
                        ],
                        '_generate': {
                            'processes': composite['processes'],
                            'topology': composite['topology'],
                            'initial_state': {}
                        }
                    }
                }
            }
        return {}


class Phage(Composer):
    def generate_processes(self, config):
        return {
            'attachment': AttachInsert(),
        }
    def generate_topology(self, config):
        return {
            'attachment': {},
        }



def test_phage():
    phage_config = {
        'agent_id': '1',
        'agents_path': ('agents',)
    }
    phage_experiment = composer_in_experiment(Phage(phage_config))

    # import ipdb; ipdb.set_trace()


if __name__ == '__main__':
    test_phage()
