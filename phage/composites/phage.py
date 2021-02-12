from vivarium.core.process import Process, Composer
from vivarium.core.composition import composer_in_experiment


class Attachment(Process):
    def ports_schema(self):
        return {}
    def next_update(self, timestep, states):
        return {}


class Insertion(Process):
    def ports_schema(self):
        return {}
    def next_update(self, timestep, states):
        return {}


class Phage(Composer):
    def generate_processes(self, config):
        return {
            'attachment': Attachment(),
            'insertion': Insertion(),
        }
    def generate_topology(self, config):
        return {
            'attachment': {},
            'insertion': {},
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
