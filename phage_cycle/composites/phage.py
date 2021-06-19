import uuid
from vivarium.core.process import Process
from vivarium.core.composer import Composer
from vivarium.core.composition import composer_in_experiment



class Phage(Composer):
    """
    TODO -- configure cell_path
    """
    defaults = {
        'cells_path': tuple()
    }
    def generate_processes(self, config):
        return {
            'attachment': AttachInsert(),
        }
    def generate_topology(self, config):
        return {
            'attachment': {
                'attach': ('attach',),
                'cells': config['cells_path'],
            },
        }


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
            'proteins': {
                'phage': {
                    'count': {
                        '_default': 0
                    },
                    'metabolite_cost': {
                        '_default': 1.0
                    }
                },
            },
            'phages': {
                '*': {}
            }
        }
    def next_update(self, timestep, states):
        # once sufficient phage protein is found, generate a Phage
        if states['proteins']['phage']['count'] > self.parameters['threshold']:
            # TODO -- remove the phage cycle protein
            phage_id = str(uuid.uuid4())

            composite = self.composer.generate({})
            return {
                'phages': {
                    '_generate': [{
                        'key': phage_id,
                        'processes': composite['processes'],
                        'topology': composite['topology'],
                        'initial_state': {}
                    }]
            }}
        return {}


class AttachInsert(Process):
    """
    This gives the Phage access to a given cell, and generates an Insertion Process inside the cell
    """
    defaults = {
        'composer': Activation,
        'gene_length': {
            'phage': 20
        }
    }

    def __init__(self, parameters=None):
        super().__init__(parameters)
        self.composer = self.parameters['composer']()

    def ports_schema(self):
        return {
            'attach': {
                '_updater': 'set',
                '_default': None,
                '_emit': True},
            'cells': {
                '*': {
                    'genes': {},
                    'proteins': {}
                }
            },
        }

    def next_update(self, timestep, states):
        # receive a cell_id to attach insertion's genes and proteins ports.
        if states['attach']:
            composite = self.composer.generate({})
            genes = [
                {
                    'key': key,
                    'state': {
                        'copy_number': 1,
                        'length': length,
                    }
                } for key, length in self.parameters['gene_length'].items()
            ]
            proteins = [
                {
                    'key': key,
                    'state': {'counts': 0}
                } for key, length in self.parameters['gene_length'].items()
            ]

            return {
                # add genes and proteins to the cell
                'cells': {
                    states['attach']: {
                        'genes': {'_add': genes},
                        'proteins': {'_add': proteins},
                        '_generate': [{
                            'processes': composite['processes'],
                            'topology': composite['topology'],
                            'initial_state': {}}
                        ]
                    }
                },
                'attach': False
            }
        return {}


def test_phage():
    phage_config = {
        'agent_id': '1',
        'agents_path': ('agents',)
    }
    phage_experiment = composer_in_experiment(Phage(phage_config))

    # import ipdb; ipdb.set_trace()


if __name__ == '__main__':
    test_phage()
