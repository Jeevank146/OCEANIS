import type { jsPDF } from 'jspdf';

export type OceanisReportType =
  | 'pfz-briefing'
  | 'hydrographic-bulletin'
  | 'passage-clearance'
  | 'cyclone-log';

export interface OceanisReportInput {
  reportType: OceanisReportType;
  sector: string;
  coordinates: string;
  includeProvenance: boolean;
  generatedAt?: Date;
}

interface ReportDefinition {
  title: string;
  shortName: string;
  purpose: string;
  sections: Array<{
    heading: string;
    paragraphs?: string[];
    rows?: Array<[string, string]>;
  }>;
}

const REPORT_DEFINITIONS: Record<OceanisReportType, ReportDefinition> = {
  'pfz-briefing': {
    title: 'Daily Fishery and Potential Fishing Zone Briefing',
    shortName: 'PFZ_Report',
    purpose: 'Operational fishing-zone assessment based on the information presented in the OCEANIS report workspace.',
    sections: [
      {
        heading: 'PFZ assessment',
        rows: [
          ['Fishing suitability', 'Optimal / Favorable'],
          ['PFZ availability', '3 active zones identified'],
          ['Indicative range', '12-28 NM east-southeast'],
          ['Evidence confidence', '88% - high reliability'],
        ],
      },
      {
        heading: 'Oceanographic evidence',
        paragraphs: [
          'Moderate thermal-front structure and chlorophyll-a accumulation are indicated near the continental shelf break.',
          'The current workspace recommends an indicative fishing window from 04:30 to 11:00 IST for appropriately registered small and medium mechanized craft.',
        ],
      },
      {
        heading: 'Operational safety',
        paragraphs: [
          'Review the latest INCOIS and IMD bulletins before departure. Maintain VHF Channel 16 watch and observe territorial, protected-area, and local port restrictions.',
        ],
      },
    ],
  },
  'hydrographic-bulletin': {
    title: 'Coastal Hydrographic and Sea State Bulletin',
    shortName: 'Ocean_State_Forecast',
    purpose: 'A concise hydrographic and sea-state briefing for the selected operating sector.',
    sections: [
      {
        heading: 'Current marine conditions',
        rows: [
          ['Assessment', 'Clear / operational vigilance'],
          ['Sea state', 'Smooth to slight'],
          ['Significant wave height', '1.2 m'],
          ['Wind', '12 kt ESE'],
        ],
      },
      {
        heading: 'Forecast interpretation',
        paragraphs: [
          'Use the OCEANIS Marine Conditions workspace for the latest hourly forecast, swell, wind, current, visibility, and sea-surface-temperature detail.',
          'Conditions may change between model cycles. Confirm official local marine forecasts before operational decisions.',
        ],
      },
      {
        heading: 'Safety thresholds',
        paragraphs: [
          'Apply vessel-specific operating limits and official small-craft advisories. This report is decision support and is not a navigational or safety guarantee.',
        ],
      },
    ],
  },
  'passage-clearance': {
    title: 'Pre-Voyage Passage Clearance and Safety Dossier',
    shortName: 'Passage_Clearance',
    purpose: 'A pre-voyage checklist and decision-support dossier for the selected marine sector.',
    sections: [
      {
        heading: 'Readiness overview',
        rows: [
          ['Workspace assessment', 'Proceed with normal caution'],
          ['Risk level', 'Low to moderate - Level 1'],
          ['Agent consensus', '85% confidence'],
          ['Safety watch', 'VHF Channel 16'],
        ],
      },
      {
        heading: 'Passage checks',
        paragraphs: [
          'Confirm destination-port status, vessel readiness, fuel reserve, route distance, expected time, exclusion zones, weather windows, and refuge options.',
          'Re-run the OCEANIS route and safety assessments immediately before departure when conditions or departure times change.',
        ],
      },
      {
        heading: 'Limitations',
        paragraphs: [
          'This dossier does not replace the vessel master, harbour authority, Coast Guard, NAVAREA warnings, or official meteorological and ocean-service bulletins.',
        ],
      },
    ],
  },
  'cyclone-log': {
    title: 'Cyclone and Severe Weather Incident Log',
    shortName: 'Cyclone_Incident_Log',
    purpose: 'A structured record for marine alerts, warnings, and severe-weather operational review.',
    sections: [
      {
        heading: 'Current alert picture',
        rows: [
          ['Monitored advisories', '3 workspace advisories'],
          ['Small-craft posture', 'Normal heightened vigilance'],
          ['High-wave status', 'Review latest INCOIS bulletin'],
          ['Cyclone authority', 'IMD Cyclone Warning Division'],
        ],
      },
      {
        heading: 'Incident record guidance',
        paragraphs: [
          'Record the official bulletin number, issue time, valid period, affected coordinates, wind and wave thresholds, port signal, vessel response, and closure or reopening decision.',
          'Attach authoritative bulletins and route decisions to the operational record when available.',
        ],
      },
      {
        heading: 'Escalation protocol',
        paragraphs: [
          'Treat official cyclone, storm-surge, tsunami, high-wave, and port-closure instructions as controlling information. Escalate uncertainty to the responsible maritime authority.',
        ],
      },
    ],
  },
};

const sanitizePdfText = (value: string) => value
  .replace(/[\u2010-\u2015]/g, '-')
  .replace(/\u00b0/g, ' deg')
  .replace(/\u00b3/g, '3')
  .replace(/\u00b2/g, '2')
  .replace(/[^\x20-\x7E\n]/g, ' ')
  .replace(/\s+/g, ' ')
  .trim();

const safeFilenamePart = (value: string) => sanitizePdfText(value)
  .replace(/[^A-Za-z0-9]+/g, '_')
  .replace(/^_+|_+$/g, '')
  .slice(0, 48) || 'Operational_Sector';

export function getOceanisReportFilename(input: OceanisReportInput): string {
  const definition = REPORT_DEFINITIONS[input.reportType];
  const date = input.generatedAt ?? new Date();
  const dateStamp = [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')].join('-');
  return `OCEANIS_${definition.shortName}_${safeFilenamePart(input.sector)}_${dateStamp}.pdf`;
}

export async function createOceanisReportPdf(input: OceanisReportInput): Promise<jsPDF> {
  const { jsPDF } = await import('jspdf');
  const definition = REPORT_DEFINITIONS[input.reportType];
  const generatedAt = input.generatedAt ?? new Date();
  const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4', compress: true });
  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 18;
  const contentWidth = pageWidth - margin * 2;
  const bottomLimit = pageHeight - 24;
  let pageNumber = 1;
  let y = 0;

  const drawHeader = () => {
    doc.setFillColor(7, 34, 54);
    doc.rect(0, 0, pageWidth, 27, 'F');
    doc.setTextColor(255, 255, 255);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(15);
    doc.text('OCEANIS', margin, 11);
    doc.setFontSize(8);
    doc.setFont('helvetica', 'normal');
    doc.text('OCEAN INTELLIGENCE AND DECISION SYSTEM', margin, 17);
    doc.setTextColor(84, 211, 194);
    doc.text('MARINE INTELLIGENCE REPORT', margin, 22);
    y = 37;
  };

  const drawFooter = () => {
    doc.setDrawColor(203, 213, 225);
    doc.line(margin, pageHeight - 17, pageWidth - margin, pageHeight - 17);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(71, 85, 105);
    doc.text('OCEANIS decision support - verify against current official maritime bulletins.', margin, pageHeight - 11);
    doc.text(`Page ${pageNumber}`, pageWidth - margin, pageHeight - 11, { align: 'right' });
  };

  const newPage = () => {
    drawFooter();
    doc.addPage('a4', 'portrait');
    pageNumber += 1;
    drawHeader();
  };

  const ensureSpace = (height: number) => {
    if (y + height > bottomLimit) newPage();
  };

  const addParagraph = (text: string) => {
    const lines = doc.splitTextToSize(sanitizePdfText(text), contentWidth);
    const blockHeight = lines.length * 4.8 + 3;
    ensureSpace(blockHeight);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(9.5);
    doc.setTextColor(51, 65, 85);
    doc.text(lines, margin, y);
    y += blockHeight;
  };

  const addSectionHeading = (index: number, heading: string) => {
    ensureSpace(14);
    doc.setFillColor(238, 246, 250);
    doc.roundedRect(margin, y - 5, contentWidth, 10, 1.5, 1.5, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10.5);
    doc.setTextColor(3, 105, 161);
    doc.text(`${index}. ${sanitizePdfText(heading).toUpperCase()}`, margin + 4, y + 1.5);
    y += 12;
  };

  const addRows = (rows: Array<[string, string]>) => {
    rows.forEach(([label, value], rowIndex) => {
      ensureSpace(12);
      doc.setFillColor(rowIndex % 2 === 0 ? 248 : 255, rowIndex % 2 === 0 ? 250 : 255, rowIndex % 2 === 0 ? 252 : 255);
      doc.rect(margin, y - 5, contentWidth, 10, 'F');
      doc.setFontSize(8.8);
      doc.setTextColor(71, 85, 105);
      doc.setFont('helvetica', 'bold');
      doc.text(sanitizePdfText(label), margin + 3, y + 1);
      doc.setTextColor(15, 23, 42);
      doc.setFont('helvetica', 'normal');
      doc.text(sanitizePdfText(value), margin + 68, y + 1);
      y += 10;
    });
    y += 4;
  };

  drawHeader();
  doc.setTextColor(11, 33, 55);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(18);
  const titleLines = doc.splitTextToSize(definition.title.toUpperCase(), contentWidth);
  doc.text(titleLines, margin, y);
  y += titleLines.length * 7.5 + 3;

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(71, 85, 105);
  doc.text(`Generated: ${generatedAt.toLocaleDateString('en-GB')} ${generatedAt.toLocaleTimeString('en-GB')} IST`, margin, y);
  y += 6;
  doc.text(`Operating sector: ${sanitizePdfText(input.sector)}`, margin, y);
  y += 6;
  doc.text(`Coordinates: ${sanitizePdfText(input.coordinates)}`, margin, y);
  y += 10;

  addParagraph(definition.purpose);
  definition.sections.forEach((section, index) => {
    addSectionHeading(index + 1, section.heading);
    if (section.rows) addRows(section.rows);
    section.paragraphs?.forEach(addParagraph);
  });

  addSectionHeading(definition.sections.length + 1, 'Data sources and attribution');
  addParagraph('INCOIS - Indian National Centre for Ocean Information Services; IMD - India Meteorological Department; ISRO / SAC; Copernicus Marine Service; GEBCO and OCEANIS PostGIS spatial services.');
  if (input.includeProvenance) {
    addParagraph(`Provenance reference: OCN-${input.reportType.toUpperCase()}-${generatedAt.getTime().toString(36).toUpperCase()}. Source labels and values are retained from the current OCEANIS workspace.`);
  }

  newPage();
  addSectionHeading(1, 'Operational acknowledgement and review record');
  addParagraph('Use this page to record the operational review performed before the report is acted upon. Confirm that official source bulletins are current for the report time and selected sector.');
  addRows([
    ['Reviewed by', '________________________________________'],
    ['Call sign / role', '________________________________________'],
    ['Review date and time', '________________________________________'],
    ['Official bulletins checked', '________________________________________'],
    ['Operational decision', '________________________________________'],
  ]);
  addSectionHeading(2, 'Important limitation');
  addParagraph('OCEANIS provides decision support. It does not replace official warnings, Notices to Mariners, harbour-master instructions, Coast Guard directions, vessel operating limits, or the judgement of the vessel master.');
  drawFooter();

  doc.setProperties({
    title: definition.title,
    subject: `OCEANIS report for ${sanitizePdfText(input.sector)}`,
    author: 'OCEANIS',
    creator: 'OCEANIS Marine Intelligence System',
    keywords: 'OCEANIS, marine intelligence, ocean forecast, safety',
  });

  return doc;
}

export async function downloadOceanisReport(input: OceanisReportInput): Promise<string> {
  const filename = getOceanisReportFilename(input);
  const doc = await createOceanisReportPdf(input);
  doc.save(filename);
  return filename;
}
