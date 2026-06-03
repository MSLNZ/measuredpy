from measuredpy import md_anchor, md_block, md_ref

@md_ref("req:calibration")
def compute_result(readings):

    md_anchor("eq:Y", "measurement model")

    with md_block("req:noise-reduction", "average repeated observations"):
        smoothed = average(readings)

    with md_block("req:correction"):
        corrected = apply_correction(smoothed)

    return corrected


class Validator:
    @md_ref("req:uncertainty")
    def estimate(self, x):
        tp_anchor("eq:u")
        return 0.1

