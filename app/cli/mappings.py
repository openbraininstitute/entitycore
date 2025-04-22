from app.db.types import ElectricalRecordingStimulusShape, ElectricalRecordingStimulusType

STIMULUS_INFO = {
    "APThreshold": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SAPThres1": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SAPThres2": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SAPThres3": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SAPTres1": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SAPTres2": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SAPTres3": {
        "shape": ElectricalRecordingStimulusShape.ramp,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "Step": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "C1HP1sec": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "C1_HP_1sec": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IRrest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SDelta": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SIDRest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SIDThres": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SIDTres": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SRac": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "pulser": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "A": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "maria-STEP": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "APDrop": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "APResh": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "C1_HP_0.5sec": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "C1step_1sec": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "C1step_ag": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "C1step_highres": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "HighResThResp": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IDRestTest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "LoOffset1": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "LoOffset3": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "Rin": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "STesteCode": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SSponAPs": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SponAPs": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SpontAPs": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "Test_eCode": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "TesteCode": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "step_1": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "step_2": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "step_3": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IV_Test": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SIV": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "APWaveform": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SAPWaveform": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "Delta": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "FirePattern": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "H10S8": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IDRest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IDThres": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IDrest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IDthresh": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IV": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IV2": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "Rac": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SetAmpl": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SetISI": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SetISITest": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "TestAmpl": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "TestRheo": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "TestSpikeRec": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SpikeRec": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "ADHPdepol": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "ADHPhyperpol": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "ADHPrest": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SSpikeRec": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SpikeRec_Ih": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SpikeRec_Kv1.1": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "scope": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "spuls": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "H40S8": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "RPip": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.voltage_clamp,
    },
    "RSealClose": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.voltage_clamp,
    },
    "RSealOpen": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.voltage_clamp,
    },
    "CalOU01": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "CalOU04": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "ElecCal": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "H20S8": {
        "shape": ElectricalRecordingStimulusShape.pulse,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "NoiseOU3": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "NoisePP": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SNoisePP": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SNoiseSpiking": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "NoiseSpiking": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "OU10Hi01": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "OU10Lo01": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "OU10Me01": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SResetITC": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "STrueNoise": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SubWhiteNoise": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "Truenoise": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "WhiteNoise": {
        "shape": ElectricalRecordingStimulusShape.noise,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "ResetITC": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SponHold25": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SponHold3": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SponHold30": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SSponHold": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SponNoHold20": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SponNoHold30": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SSponNoHold": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "Spontaneous": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "StartHold": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "StartNoHold": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "StartStandeCode": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "VacuumPulses": {
        "shape": ElectricalRecordingStimulusShape.constant,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "sAHP": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IRdepol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IRhyperpol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IDdepol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "IDhyperpol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SsAHP": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "HyperDePol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "DeHyperPol": {
        "shape": ElectricalRecordingStimulusShape.two_steps,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "NegCheops": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "NegCheops1": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "NegCheops2": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "NegCheops3": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "NegCheops4": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "NegCheops5": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "PosCheops": {
        "shape": ElectricalRecordingStimulusShape.cheops,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SineSpec": {
        "shape": ElectricalRecordingStimulusShape.sinusoidal,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SSineSpec": {
        "shape": ElectricalRecordingStimulusShape.sinusoidal,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "Pulse": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "S2": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "s2": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "S30": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "SIne20Hz": {
        "shape": ElectricalRecordingStimulusShape.other,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
    "A___.ibw": {
        "shape": ElectricalRecordingStimulusShape.step,
        "type": ElectricalRecordingStimulusType.current_clamp,
    },
}
