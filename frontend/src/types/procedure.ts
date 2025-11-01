export enum ProcedureType {
  EBUS = 'EBUS',
  NAVIGATIONAL = 'NAVIGATIONAL',
  ROBOTIC = 'ROBOTIC',
  THERAPEUTIC = 'THERAPEUTIC'
}

export type CommonAnnotationFields = {
  date: string;
  operators?: string[];
  sedation?: string;
  complications?: string;
  notes?: string;
};

export type EBUSDetails = {
  nodeStations: string[];
  needleGauge?: '19G' | '21G' | '22G' | '25G';
  totalPasses?: number;
  rosePerformed?: boolean;
  adequacy?:
    | 'Adequate'
    | 'Inadequate'
    | 'Atypical'
    | 'Suspicious'
    | 'Malignant'
    | 'Benign';
};

export type NavigationalDetails = {
  lobe?: string;
  segment?: string;
  lesionSizeMm?: number;
  distanceToPleuraMm?: number;
  radialEbusUsed?: boolean;
  coneBeamUsed?: boolean;
};

export type RoboticDetails = {
  platform?: 'Ion' | 'Monarch' | 'Other';
  lobe?: string;
  segment?: string;
  lesionSizeMm?: number;
  ctToBodyDivergenceMm?: number;
  radialEbusUsed?: boolean;
  coneBeamUsed?: boolean;
};

export type TherapeuticDetails = {
  interventions: Array<
    | 'APC'
    | 'Cryo'
    | 'Laser'
    | 'BalloonDilation'
    | 'MechanicalDebulking'
    | 'StentPlacement'
    | 'Other'
  >;
  stent?: {
    location?: string;
    type?: string;
    diameterMm?: number;
    lengthMm?: number;
  };
  hemostasisAchieved?: boolean;
};

export type ProcedureDetails =
  | ({ procedureType: ProcedureType.EBUS } & EBUSDetails)
  | ({ procedureType: ProcedureType.NAVIGATIONAL } & NavigationalDetails)
  | ({ procedureType: ProcedureType.ROBOTIC } & RoboticDetails)
  | ({ procedureType: ProcedureType.THERAPEUTIC } & TherapeuticDetails);

export type AnnotationFormData = CommonAnnotationFields & {
  procedureType: ProcedureType;
  details: EBUSDetails | NavigationalDetails | RoboticDetails | TherapeuticDetails;
};
