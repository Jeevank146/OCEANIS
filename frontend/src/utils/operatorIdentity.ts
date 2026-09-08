export interface OperatorIdentity {
  location: string;
  sector: string;
  operatorName: string;
  role: string;
  displayLabel: string;
  callSign: string;
}

/**
 * Deterministic location-aware maritime operator identity generator.
 * Strictly adheres to requirement: NO static 'Cmdr. R. Verma'.
 * Uses fictional/system-generated operational identities (e.g. 'Duty Officer', 'Operations Officer').
 */
export function getOperatorIdentity(
  locationName?: string,
  cityName?: string,
  isOffshore?: boolean,
  isInland?: boolean,
  status?: string
): OperatorIdentity {
  const loc = (cityName || locationName || 'Coastal Sector').replace(/\s*\([^)]*\)/g, '').trim();

  if (isInland || status === 'INLAND') {
    return {
      location: loc || 'Inland Sector',
      sector: `${loc || 'Inland'} Sector`,
      operatorName: 'Inland Command Officer',
      role: 'Inland Operations',
      displayLabel: `${loc || 'Inland'} Sector`,
      callSign: `${(loc || 'INL').toUpperCase().slice(0, 3)}-INL-01`,
    };
  }

  if (
    isOffshore ||
    status === 'OFFSHORE' ||
    status === 'VALID_MARINE' ||
    loc.toLowerCase().includes('offshore') ||
    loc.toLowerCase().includes('waypoint') ||
    loc.toLowerCase().includes('marine')
  ) {
    return {
      location: loc || 'Offshore Sector',
      sector: 'Offshore Marine Sector',
      operatorName: 'Marine Operations Officer',
      role: 'Offshore Sector',
      displayLabel: 'Offshore Marine Sector',
      callSign: 'MAR-OPS-99',
    };
  }

  // Coastal / Port location
  return {
    location: loc || 'Coastal Sector',
    sector: `${loc || 'Coastal'} Sector`,
    operatorName: `${loc || 'Coastal'} Duty Officer`,
    role: `${loc || 'Coastal'} Sector`,
    displayLabel: `${loc || 'Coastal'} Sector`,
    callSign: `${(loc || 'OPS').toUpperCase().slice(0, 3)}-OPS-01`,
  };
}
