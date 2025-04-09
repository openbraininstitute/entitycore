from enum import StrEnum

from app.db.types import (
    ElectricalRecordingStimulusShape,
    ElectricalRecordingStimulusType,
    MeasurementStatistic,
    MeasurementUnit,
    StructuralDomain,
)


class ECode(StrEnum):
    """Curated ecodes."""

    ap_drop = "APDrop"
    ap_resh = "APResh"
    ap_threshold = "APThreshold"
    ap_waveform = "APWaveform"
    adhp_depol = "ADHPdepol"
    adhp_hyperpol = "ADHPhyperpol"
    adhp_rest = "ADHPrest"
    calou01 = "CalOU01"
    calou04 = "CalOU04"
    c1hp = "C1HP"
    c1step = "C1step"
    delta = "Delta"
    delta_custom = "DeltaCustom"
    de_hyper_pol = "DeHyperPol"
    elec_cal = "ElecCal"
    fire_pattern = "FirePattern"
    generic_step = "GenericStep"
    h10s8 = "H10S8"
    h20s8 = "H20S8"
    h40s8 = "H40S8"
    high_res_thresp = "HighResThResp"
    hyper_depol = "HyperDePol"
    id_depol = "IDdepol"
    id_hyperpol = "IDhyperpol"
    id_rest = "IDRest"
    id_threshold = "IDThreshold"
    ir_depol = "IRdepol"
    ir_hyperpol = "IRhyperpol"
    pos_cheops = "PosCheops"
    rac = "Rac"
    rpip = "RPip"
    rseal_close = "RSealClose"
    rseal_open = "RSealOpen"
    scope = "scope"
    set_ampl = "SetAmpl"
    sponaps = "SponAPs"
    spuls = "spuls"
    step = "Step"
    lo_offset = "LoOffset"
    iv = "IV"
    rin = "Rin"
    neg_cheops = "NegCheops"
    noise_pp = "NoisePP"
    noise_spiking = "NoiseSpiking"
    noise_ou3 = "NoiseOU3"
    ou10 = "OU10"
    pulser = "pulser"
    ramp_sine_20 = "RampSine20Hz"
    reset_itc = "ResetITC"
    s2 = "S2Protocol"
    s30 = "S30"
    sahp = "sAHP"
    set_isi = "SetISI"
    sine_spec = "SineSpec"
    spike_rec = "SpikeRec"
    spike_rec_ih = "SpikeRec_Ih"
    spike_rec_kv1 = "SpikeRec_Kv1.1"
    spontaneous = "Spontaneous"
    spontaneous_no_hold = "SpontaneousNoHold"
    sub_white_noise = "SubWhiteNoise"
    start_hold = "StartHold"
    start_no_hold = "StartNoHold"
    test_ampl = "TestAmpl"
    test_rheo = "TestRheo"
    test_spike_rec = "TestSpikeRec"
    true_noise = "Truenoise"
    vacuum_pulses = "VacuumPulses"
    white_noise = "WhiteNoise"


STIMULUS_INFO = {
    "APThreshold": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ap_threshold,
    },
    "SAPThres1": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ap_threshold,
    },
    "SAPThres2": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ap_threshold,
    },
    "SAPThres3": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ap_threshold,
    },
    "SAPTres1": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ap_threshold,
    },
    "SAPTres2": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ap_threshold,
    },
    "SAPTres3": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ap_threshold,
    },
    "Step": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.step,
    },
    "Step_150": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.step,
    },
    "Step_200": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.step,
    },
    "Step_250": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.step,
    },
    "Step_150_hyp": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.step,
    },
    "Step_200_hyp": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.step,
    },
    "Step_250_hyp": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.step,
    },
    "C1HP1sec": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.c1hp,
    },
    "C1_HP_1sec": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.c1hp,
    },
    "IRrest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.id_rest,
    },
    "SDelta": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.delta,
    },
    "SIDRest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.id_rest,
    },
    "SIDThres": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.id_threshold,
    },
    "SIDTres": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.id_threshold,
    },
    "SRac": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.rac,
    },
    "pulser": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.pulser,
    },
    "A": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.generic_step,
    },
    "maria-STEP": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.generic_step,
    },
    "APDrop": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ap_drop,
    },
    "APResh": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ap_resh,
    },
    "C1_HP_0.5sec": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.c1hp,
    },
    "C1step_1sec": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.c1step,
    },
    "C1step_ag": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.c1step,
    },
    "C1step_highres": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.c1step,
    },
    "HighResThResp": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.high_res_thresp,
    },
    "IDRestTest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.generic_step,
    },
    "LoOffset1": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.lo_offset,
    },
    "LoOffset3": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.lo_offset,
    },
    "Rin": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.rin,
    },
    "STesteCode": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.generic_step,
    },
    "SSponAPs": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.sponaps,
    },
    "SponAPs": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.sponaps,
    },
    "SpontAPs": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.sponaps,
    },
    "Test_eCode": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.generic_step,
    },
    "TesteCode": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.generic_step,
    },
    "step_1": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.generic_step,
    },
    "step_2": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.generic_step,
    },
    "step_3": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.generic_step,
    },
    "IV_Test": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.generic_step,
    },
    "SIV": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.iv,
    },
    "APWaveform": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ap_waveform,
    },
    "SAPWaveform": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ap_waveform,
    },
    "Delta": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.delta,
    },
    "FirePattern": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.fire_pattern,
    },
    "H10S8": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.h10s8,
    },
    "H20S8": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.h20s8,
    },
    "H40S8": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.h40s8,
    },
    "IDRest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.id_rest,
    },
    "IDThres": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.id_threshold,
    },
    "IDThresh": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.id_threshold,
    },
    "IDrest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.id_rest,
    },
    "IDthresh": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.id_threshold,
    },
    "IV": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.iv,
    },
    "IV2": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.iv,
    },
    "IV_-120": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.iv,
    },
    "IV_-120_hyp": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.iv,
    },
    "IV_-140": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.iv,
    },
    "Rac": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.rac,
    },
    "RMP": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spontaneous_no_hold,
    },
    "SetAmpl": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.set_ampl,
    },
    "SetISI": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.set_isi,
    },
    "SetISITest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.set_isi,
    },
    "TestAmpl": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.test_ampl,
    },
    "TestRheo": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.test_rheo,
    },
    "TestSpikeRec": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.test_spike_rec,
    },
    "SpikeRec": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spike_rec,
    },
    "ADHPdepol": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.adhp_depol,
    },
    "ADHPhyperpol": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.adhp_hyperpol,
    },
    "ADHPrest": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.adhp_rest,
    },
    "SSpikeRec": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spike_rec,
    },
    "SpikeRec_Ih": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spike_rec_ih,
    },
    "SpikeRec_Kv1.1": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spike_rec_kv1,
    },
    "scope": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.scope,
    },
    "spuls": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spuls,
    },
    "RPip": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.voltage_clamp,
        "ecode": ECode.rpip,
    },
    "RSealClose": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.voltage_clamp,
        "ecode": ECode.rseal_close,
    },
    "RSealOpen": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.voltage_clamp,
        "ecode": ECode.rseal_open,
    },
    "CalOU01": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.calou01,
    },
    "CalOU04": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.calou04,
    },
    "ElecCal": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.elec_cal,
    },
    "NoiseOU3": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.noise_ou3,
    },
    "NoisePP": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.noise_pp,
    },
    "SNoisePP": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.noise_pp,
    },
    "SNoiseSpiking": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.noise_spiking,
    },
    "NoiseSpiking": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.noise_spiking,
    },
    "OU10Hi01": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ou10,
    },
    "OU10Lo01": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ou10,
    },
    "OU10Me01": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ou10,
    },
    "SResetITC": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.reset_itc,
    },
    "STrueNoise": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.true_noise,
    },
    "SubWhiteNoise": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.sub_white_noise,
    },
    "Truenoise": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.true_noise,
    },
    "WhiteNoise": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.white_noise,
    },
    "ResetITC": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.reset_itc,
    },
    "SponHold25": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spontaneous,
    },
    "SponHold3": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spontaneous,
    },
    "SponHold30": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spontaneous,
    },
    "SSponHold": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spontaneous,
    },
    "SponNoHold20": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spontaneous_no_hold,
    },
    "SponNoHold30": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spontaneous_no_hold,
    },
    "SSponNoHold": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spontaneous_no_hold,
    },
    "Spontaneous": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spontaneous,
    },
    "hold_dep": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spontaneous,
    },
    "hold_hyp": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.spontaneous,
    },
    "StartHold": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.start_hold,
    },
    "StartNoHold": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.start_no_hold,
    },
    "StartStandeCode": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.start_no_hold,
    },
    "VacuumPulses": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.vacuum_pulses,
    },
    "sAHP": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.sahp,
    },
    "IRdepol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ir_depol,
    },
    "IRhyperpol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ir_hyperpol,
    },
    "IDdepol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.id_depol,
    },
    "IDhyperpol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.id_hyperpol,
    },
    "SsAHP": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.sahp,
    },
    "HyperDePol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.hyper_depol,
    },
    "DeHyperPol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.de_hyper_pol,
    },
    "NegCheops": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.neg_cheops,
    },
    "NegCheops1": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.neg_cheops,
    },
    "NegCheops2": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.neg_cheops,
    },
    "NegCheops3": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.neg_cheops,
    },
    "NegCheops4": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.neg_cheops,
    },
    "NegCheops5": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.neg_cheops,
    },
    "PosCheops": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.pos_cheops,
    },
    "Rin_dep": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.rin,
    },
    "Rin_hyp": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.rin,
    },
    "SineSpec": {
        "shape": ElectricalRecordingStimulusShape.sinusoidal,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.sine_spec,
    },
    "SSineSpec": {
        "shape": ElectricalRecordingStimulusShape.sinusoidal,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.sine_spec,
    },
    "Pulse": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.delta_custom,
    },
    "S2": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.s2,
    },
    "s2": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.s2,
    },
    "S30": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.s30,
    },
    "SIne20Hz": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.ramp_sine_20,
    },
    "A___.ibw": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
        "ecode": ECode.generic_step,
    },
}

MEASUREMENT_UNIT_MAP = {item.value: item for item in MeasurementUnit}
MEASUREMENT_STATISTIC_MAP = {item.value: item for item in MeasurementStatistic} | {
    "standard deviation": MeasurementStatistic.standard_deviation,
}
STRUCTURAL_DOMAIN_MAP = {
    "Axon": StructuralDomain.axon,
    "ApicalDendrite": StructuralDomain.apical_dendrite,
    "BasalDendrite": StructuralDomain.basal_dendrite,
    None: None,
}
