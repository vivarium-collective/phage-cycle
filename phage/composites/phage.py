from vivarium.core.process import Process, Composite


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


class Phage(Composite):
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
