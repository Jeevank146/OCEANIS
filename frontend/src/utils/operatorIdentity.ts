export interface OperatorIdentity {
  location: string;
  sector: string;
  operatorName: string;
  role: string;
  displayLabel: string;
  callSign: string;
}

/**
 * Deterministic location-aware maritime operational identity generator.
 * Strictly adheres to requirement:
 * - NO hardcoded 'Cmdr. R. Verma'
 * - NO fake officer titles (Cmdr. X, Duty Officer, etc.)
 * - For coastal: '<Resolved Location> Marine Operations'
 * - For offshore: 'Offshore Marine Operations'
 * - For inland: 'Inland Operations'
 * - For unknown/unresolved: 'Marine Operations'
 */
export function getOperatorIdentity(
  locationName?: string,
  cityName?: string,
  isOffshore?: boolean,
  isInland?: boolean,
  status?: string,
  configuredOperator?: string
): OperatorIdentity {
  if (configuredOperator && configuredOperator.trim()) {
    const loc = (cityName || locationName || 'Coastal Sector').trim();
    return {
      location: loc,
      sector: loc + ' Sector',
      operatorName: configuredOperator.trim(),
      role: 'Configured Operator',
      displayLabel: configuredOperator.trim(),
      callSign: 'OPS-USR-01',
    };
  }

  const rawLoc = (cityName || locationName || '').replace(/\s*\([^)]*\)/g, '').trim();

  if (isInland || status === 'INLAND') {
    const loc = rawLoc || 'Inland';
    return {
      location: loc + ' Area',
      sector: 'Inland Operations',
      operatorName: loc + ' Inland Operations',
      role: 'Inland Operations',
      displayLabel: loc + ' Inland Operations',
      callSign: loc.toUpperCase().slice(0, 3) + '-INL-01',
    };
  }

  if (
    isOffshore ||
    status === 'OFFSHORE' ||
    status === 'VALID_MARINE' ||
    rawLoc.toLowerCase().includes('offshore') ||
    rawLoc.toLowerCase().includes('waypoint') ||
    rawLoc.toLowerCase().includes('marine')
  ) {
    return {
      location: rawLoc || 'Offshore Sector',
      sector: 'Offshore Marine Operations',
      operatorName: 'Offshore Marine Operations',
      role: 'Offshore Marine Operations',
      displayLabel: 'Offshore Marine Operations',
      callSign: 'MAR-OPS-99',
    };
  }

  if (rawLoc) {
    return {
      location: rawLoc,
      sector: rawLoc + ' Sector',
      operatorName: rawLoc + ' Marine Operations',
      role: rawLoc + ' Marine Operations',
      displayLabel: rawLoc + ' Marine Operations',
      callSign: rawLoc.toUpperCase().slice(0, 3) + '-OPS-01',
    };
  }

  // Unknown / Unresolved location
  return {
    location: 'Marine Operations',
    sector: 'Marine Operations',
    operatorName: 'Marine Operations',
    role: 'Marine Operations',
    displayLabel: 'Marine Operations',
    callSign: 'MAR-OPS-01',
  };
}
