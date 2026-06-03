def tp_anchor(label, note=None):
    pass

from contextlib import contextmanager

@contextmanager
def tp_block(label, note=None):
    yield

def tp_ref(label):
    def decorator(obj):
        return obj
    return decorator
    
# @tp_ref("req:calibration")
# def compute_result(readings):
    # with tp_block("req:noise-reduction", "reduce random noise by averaging"):
        # readings = average(readings)

    # with tp_block("req:correction-factor"):
        # readings = apply_correction(readings)

    # return readings