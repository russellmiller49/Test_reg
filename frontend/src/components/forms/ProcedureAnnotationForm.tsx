'use client';

import React from 'react';
import { Controller, useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  Box,
  Button,
  Checkbox,
  Divider,
  FormControl,
  FormHelperText,
  InputLabel,
  ListItemText,
  MenuItem,
  Select,
  SelectChangeEvent,
  TextField,
  Typography
} from '@mui/material';
import {
  AnnotationFormData,
  ProcedureType
} from '@/types/procedure';

const CommonSchema = z.object({
  date: z.string().min(1, 'Date is required'),
  operators: z.array(z.string()).optional(),
  sedation: z.string().optional(),
  complications: z.string().optional(),
  notes: z.string().optional()
});

const FormSchema = CommonSchema.extend({
  procedureType: z.nativeEnum(ProcedureType),
  details: z.record(z.any()).default({})
});

type FormSchemaType = z.infer<typeof FormSchema>;

const LYMPH_NODE_STATIONS = [
  '2R',
  '2L',
  '4R',
  '4L',
  '7',
  '10R',
  '10L',
  '11R',
  '11L',
  '12R',
  '12L'
];

const LOBES = ['RUL', 'RML', 'RLL', 'LUL', 'LLL'];

const defaultDetailsByType: Record<ProcedureType, Record<string, unknown>> = {
  [ProcedureType.EBUS]: { nodeStations: [] },
  [ProcedureType.NAVIGATIONAL]: {},
  [ProcedureType.ROBOTIC]: {},
  [ProcedureType.THERAPEUTIC]: { interventions: [], stent: {} }
};

export type ProcedureAnnotationFormProps = {
  defaultValues?: Partial<AnnotationFormData>;
  onSubmit: (data: AnnotationFormData) => Promise<void> | void;
  submitting?: boolean;
};

function asBooleanSelectValue(value: boolean | undefined) {
  if (value === undefined) {
    return '';
  }
  return value ? 'true' : 'false';
}

function handleBooleanSelectChange(event: SelectChangeEvent<string>, onChange: (val: boolean | undefined) => void) {
  const raw = event.target.value;
  if (raw === '') {
    onChange(undefined);
  } else {
    onChange(raw === 'true');
  }
}

export default function ProcedureAnnotationForm({
  defaultValues,
  onSubmit,
  submitting
}: ProcedureAnnotationFormProps) {
  const {
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors }
  } = useForm<FormSchemaType>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      date: new Date().toISOString().slice(0, 10),
      procedureType: ProcedureType.EBUS,
      details: defaultDetailsByType[ProcedureType.EBUS],
      ...defaultValues
    }
  });

  const procedureType = watch('procedureType');

  const previousTypeRef = React.useRef(procedureType);
  React.useEffect(() => {
    if (previousTypeRef.current !== procedureType) {
      previousTypeRef.current = procedureType;
      setValue('details', defaultDetailsByType[procedureType], { shouldDirty: false });
    }
  }, [procedureType, setValue]);

  const onFormSubmit = React.useCallback(
    (values: FormSchemaType) => {
      const normalized: AnnotationFormData = {
        date: values.date,
        operators: values.operators?.filter((entry) => entry.trim().length > 0).map((entry) => entry.trim()),
        sedation: values.sedation || undefined,
        complications: values.complications || undefined,
        notes: values.notes || undefined,
        procedureType: values.procedureType,
        details: {}
      };

      const details: Record<string, unknown> = { ...defaultDetailsByType[values.procedureType], ...values.details };

      const coerceNumber = (value: unknown) => {
        if (value === '' || value === null || value === undefined) {
          return undefined;
        }
        const parsed = Number(value);
        return Number.isNaN(parsed) ? undefined : parsed;
      };

      switch (values.procedureType) {
        case ProcedureType.EBUS:
          details.totalPasses = coerceNumber(details.totalPasses);
          break;
        case ProcedureType.NAVIGATIONAL:
          details.lesionSizeMm = coerceNumber(details.lesionSizeMm);
          details.distanceToPleuraMm = coerceNumber(details.distanceToPleuraMm);
          break;
        case ProcedureType.ROBOTIC:
          details.lesionSizeMm = coerceNumber(details.lesionSizeMm);
          details.ctToBodyDivergenceMm = coerceNumber(details.ctToBodyDivergenceMm);
          break;
        case ProcedureType.THERAPEUTIC: {
          const stent = details.stent as Record<string, unknown> | undefined;
          if (stent) {
            stent.diameterMm = coerceNumber(stent.diameterMm);
            stent.lengthMm = coerceNumber(stent.lengthMm);
          }
          break;
        }
        default:
          break;
      }

      normalized.details = details;
      onSubmit(normalized);
    },
    [onSubmit]
  );

  const renderEBUS = () => (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6">EBUS Details</Typography>
      <Controller
        name="details.nodeStations"
        control={control}
        defaultValue={[]}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="stations-label">Node Stations</InputLabel>
            <Select
              labelId="stations-label"
              multiple
              value={field.value ?? []}
              onChange={(event) => field.onChange(event.target.value)}
              renderValue={(selected) => (selected as string[]).join(', ')}
            >
              {LYMPH_NODE_STATIONS.map((station) => (
                <MenuItem key={station} value={station}>
                  <Checkbox checked={(field.value ?? []).includes(station)} />
                  <ListItemText primary={station} />
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>Select all sampled stations</FormHelperText>
          </FormControl>
        )}
      />
      <Controller
        name="details.needleGauge"
        control={control}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="needle-label">Needle Gauge</InputLabel>
            <Select labelId="needle-label" value={field.value ?? ''} onChange={field.onChange}>
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              {['19G', '21G', '22G', '25G'].map((gauge) => (
                <MenuItem key={gauge} value={gauge}>
                  {gauge}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      />
      <Controller
        name="details.totalPasses"
        control={control}
        render={({ field }) => (
          <TextField
            type="number"
            label="Total Passes"
            fullWidth
            margin="normal"
            value={field.value ?? ''}
            onChange={(event) => field.onChange(event.target.value === '' ? undefined : Number(event.target.value))}
          />
        )}
      />
      <Controller
        name="details.rosePerformed"
        control={control}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="rose-label">ROSE Performed</InputLabel>
            <Select
              labelId="rose-label"
              value={asBooleanSelectValue(field.value)}
              onChange={(event) => handleBooleanSelectChange(event, field.onChange)}
            >
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>
        )}
      />
      <Controller
        name="details.adequacy"
        control={control}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="adequacy-label">Adequacy</InputLabel>
            <Select labelId="adequacy-label" value={field.value ?? ''} onChange={field.onChange}>
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              {['Adequate', 'Inadequate', 'Atypical', 'Suspicious', 'Malignant', 'Benign'].map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      />
    </Box>
  );

  const renderNavigational = () => (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6">Navigational Details</Typography>
      <Controller
        name="details.lobe"
        control={control}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="nav-lobe-label">Lobe</InputLabel>
            <Select labelId="nav-lobe-label" value={field.value ?? ''} onChange={field.onChange}>
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              {LOBES.map((lobe) => (
                <MenuItem key={lobe} value={lobe}>
                  {lobe}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      />
      <Controller
        name="details.segment"
        control={control}
        render={({ field }) => (
          <TextField label="Segment" fullWidth margin="normal" value={field.value ?? ''} onChange={field.onChange} />
        )}
      />
      <Controller
        name="details.lesionSizeMm"
        control={control}
        render={({ field }) => (
          <TextField
            type="number"
            label="Lesion Size (mm)"
            fullWidth
            margin="normal"
            value={field.value ?? ''}
            onChange={(event) => field.onChange(event.target.value === '' ? undefined : Number(event.target.value))}
          />
        )}
      />
      <Controller
        name="details.distanceToPleuraMm"
        control={control}
        render={({ field }) => (
          <TextField
            type="number"
            label="Distance to Pleura (mm)"
            fullWidth
            margin="normal"
            value={field.value ?? ''}
            onChange={(event) => field.onChange(event.target.value === '' ? undefined : Number(event.target.value))}
          />
        )}
      />
      <Controller
        name="details.radialEbusUsed"
        control={control}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="nav-radial-label">Radial EBUS Used</InputLabel>
            <Select
              labelId="nav-radial-label"
              value={asBooleanSelectValue(field.value)}
              onChange={(event) => handleBooleanSelectChange(event, field.onChange)}
            >
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>
        )}
      />
      <Controller
        name="details.coneBeamUsed"
        control={control}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="nav-conebeam-label">Cone-beam CT Used</InputLabel>
            <Select
              labelId="nav-conebeam-label"
              value={asBooleanSelectValue(field.value)}
              onChange={(event) => handleBooleanSelectChange(event, field.onChange)}
            >
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>
        )}
      />
    </Box>
  );

  const renderRobotic = () => (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6">Robotic Details</Typography>
      <Controller
        name="details.platform"
        control={control}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="robotic-platform-label">Platform</InputLabel>
            <Select
              labelId="robotic-platform-label"
              value={field.value ?? ''}
              onChange={field.onChange}
            >
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              {['Ion', 'Monarch', 'Other'].map((platform) => (
                <MenuItem key={platform} value={platform}>
                  {platform}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      />
      <Controller
        name="details.lobe"
        control={control}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="robotic-lobe-label">Lobe</InputLabel>
            <Select labelId="robotic-lobe-label" value={field.value ?? ''} onChange={field.onChange}>
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              {LOBES.map((lobe) => (
                <MenuItem key={lobe} value={lobe}>
                  {lobe}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
      />
      <Controller
        name="details.segment"
        control={control}
        render={({ field }) => (
          <TextField label="Segment" fullWidth margin="normal" value={field.value ?? ''} onChange={field.onChange} />
        )}
      />
      <Controller
        name="details.lesionSizeMm"
        control={control}
        render={({ field }) => (
          <TextField
            type="number"
            label="Lesion Size (mm)"
            fullWidth
            margin="normal"
            value={field.value ?? ''}
            onChange={(event) => field.onChange(event.target.value === '' ? undefined : Number(event.target.value))}
          />
        )}
      />
      <Controller
        name="details.ctToBodyDivergenceMm"
        control={control}
        render={({ field }) => (
          <TextField
            type="number"
            label="CT-to-body divergence (mm)"
            fullWidth
            margin="normal"
            value={field.value ?? ''}
            onChange={(event) => field.onChange(event.target.value === '' ? undefined : Number(event.target.value))}
          />
        )}
      />
      <Controller
        name="details.radialEbusUsed"
        control={control}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="robotic-radial-label">Radial EBUS Used</InputLabel>
            <Select
              labelId="robotic-radial-label"
              value={asBooleanSelectValue(field.value)}
              onChange={(event) => handleBooleanSelectChange(event, field.onChange)}
            >
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>
        )}
      />
      <Controller
        name="details.coneBeamUsed"
        control={control}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="robotic-conebeam-label">Cone-beam CT Used</InputLabel>
            <Select
              labelId="robotic-conebeam-label"
              value={asBooleanSelectValue(field.value)}
              onChange={(event) => handleBooleanSelectChange(event, field.onChange)}
            >
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>
        )}
      />
    </Box>
  );

  const renderTherapeutic = () => (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6">Therapeutic Details</Typography>
      <Controller
        name="details.interventions"
        control={control}
        defaultValue={[]}
        render={({ field }) => {
          const options = [
            'APC',
            'Cryo',
            'Laser',
            'BalloonDilation',
            'MechanicalDebulking',
            'StentPlacement',
            'Other'
          ];
          return (
            <FormControl fullWidth margin="normal">
              <InputLabel id="therapeutic-interventions-label">Interventions</InputLabel>
              <Select
                labelId="therapeutic-interventions-label"
                multiple
                value={field.value ?? []}
                onChange={(event) => field.onChange(event.target.value)}
                renderValue={(selected) => (selected as string[]).join(', ')}
              >
                {options.map((option) => (
                  <MenuItem key={option} value={option}>
                    <Checkbox checked={(field.value ?? []).includes(option)} />
                    <ListItemText primary={option} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          );
        }}
      />
      <Typography variant="subtitle1" sx={{ mt: 2 }}>
        Stent (optional)
      </Typography>
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2, mt: 1 }}>
        <Controller
          name="details.stent.location"
          control={control}
          render={({ field }) => (
            <TextField label="Location" value={field.value ?? ''} onChange={field.onChange} />
          )}
        />
        <Controller
          name="details.stent.type"
          control={control}
          render={({ field }) => <TextField label="Type" value={field.value ?? ''} onChange={field.onChange} />}
        />
        <Controller
          name="details.stent.diameterMm"
          control={control}
          render={({ field }) => (
            <TextField
              type="number"
              label="Diameter (mm)"
              value={field.value ?? ''}
              onChange={(event) => field.onChange(event.target.value === '' ? undefined : Number(event.target.value))}
            />
          )}
        />
        <Controller
          name="details.stent.lengthMm"
          control={control}
          render={({ field }) => (
            <TextField
              type="number"
              label="Length (mm)"
              value={field.value ?? ''}
              onChange={(event) => field.onChange(event.target.value === '' ? undefined : Number(event.target.value))}
            />
          )}
        />
      </Box>
      <Controller
        name="details.hemostasisAchieved"
        control={control}
        render={({ field }) => (
          <FormControl fullWidth margin="normal">
            <InputLabel id="therapeutic-hemostasis-label">Hemostasis Achieved</InputLabel>
            <Select
              labelId="therapeutic-hemostasis-label"
              value={asBooleanSelectValue(field.value)}
              onChange={(event) => handleBooleanSelectChange(event, field.onChange)}
            >
              <MenuItem value="">
                <em>—</em>
              </MenuItem>
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>
        )}
      />
    </Box>
  );

  const renderCommon = () => (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6">Common</Typography>
      <Controller
        name="date"
        control={control}
        render={({ field }) => (
          <TextField
            type="date"
            label="Date"
            fullWidth
            margin="normal"
            InputLabelProps={{ shrink: true }}
            {...field}
          />
        )}
      />
      {errors.date && (
        <Typography variant="body2" color="error">
          {errors.date.message}
        </Typography>
      )}
      <Controller
        name="operators"
        control={control}
        render={({ field }) => (
          <TextField
            label="Operators (comma separated)"
            fullWidth
            margin="normal"
            value={(field.value ?? []).join(', ')}
            onChange={(event) =>
              field.onChange(
                event.target.value
                  .split(',')
                  .map((item) => item.trim())
                  .filter((item) => item.length > 0)
              )
            }
          />
        )}
      />
      <Controller
        name="sedation"
        control={control}
        render={({ field }) => (
          <TextField label="Sedation / Anesthesia" fullWidth margin="normal" value={field.value ?? ''} onChange={field.onChange} />
        )}
      />
      <Controller
        name="complications"
        control={control}
        render={({ field }) => (
          <TextField
            label="Complications"
            multiline
            minRows={2}
            fullWidth
            margin="normal"
            value={field.value ?? ''}
            onChange={field.onChange}
          />
        )}
      />
      <Controller
        name="notes"
        control={control}
        render={({ field }) => (
          <TextField
            label="Notes"
            multiline
            minRows={3}
            fullWidth
            margin="normal"
            value={field.value ?? ''}
            onChange={field.onChange}
          />
        )}
      />
    </Box>
  );

  return (
    <Box component="form" onSubmit={handleSubmit(onFormSubmit)} sx={{ maxWidth: 900, width: '100%', mx: 'auto' }}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        New Procedure Annotation
      </Typography>
      <FormControl fullWidth margin="normal" error={Boolean(errors.procedureType)}>
        <InputLabel id="procedure-type-label">Procedure Type</InputLabel>
        <Controller
          name="procedureType"
          control={control}
          render={({ field }) => (
            <Select
              labelId="procedure-type-label"
              {...field}
              onChange={(event) => field.onChange(event.target.value as ProcedureType)}
            >
              <MenuItem value={ProcedureType.EBUS}>EBUS</MenuItem>
              <MenuItem value={ProcedureType.NAVIGATIONAL}>Navigational</MenuItem>
              <MenuItem value={ProcedureType.ROBOTIC}>Robotic</MenuItem>
              <MenuItem value={ProcedureType.THERAPEUTIC}>Therapeutic</MenuItem>
            </Select>
          )}
        />
        {errors.procedureType && <FormHelperText>{errors.procedureType.message}</FormHelperText>}
      </FormControl>

      <Divider sx={{ my: 2 }} />

      {procedureType === ProcedureType.EBUS && renderEBUS()}
      {procedureType === ProcedureType.NAVIGATIONAL && renderNavigational()}
      {procedureType === ProcedureType.ROBOTIC && renderRobotic()}
      {procedureType === ProcedureType.THERAPEUTIC && renderTherapeutic()}

      <Divider sx={{ my: 2 }} />

      {renderCommon()}

      <Box sx={{ mt: 4, display: 'flex', gap: 2 }}>
        <Button type="submit" variant="contained" disabled={submitting}>
          {submitting ? 'Saving...' : 'Save'}
        </Button>
        <Button type="button" variant="outlined" onClick={() => window.history.back()}>
          Cancel
        </Button>
      </Box>
    </Box>
  );
}
