export type VerificationResult = "supported" | "refuted" | "not-enough-info";

export type Verification = {
  id: string;
  type: "claim" | "question";
  text: string;
  result: VerificationResult;
  confidence: number;
  date: string;
  time: string;
};

export const currentUser = {
  name: "Shivaleela",
  initial: "S",
  email: "shivaleela@verimind.ai",
};

export const stats = [
  { key: "total", label: "Total Verifications", value: 32 },
  { key: "supported", label: "Supported", value: 18 },
  { key: "refuted", label: "Refuted", value: 8 },
  { key: "unknown", label: "Not Enough Info", value: 6 },
] as const;

export const weeklyActivity = [
  { day: "Mon", supported: 3, refuted: 1, unknown: 1 },
  { day: "Tue", supported: 4, refuted: 2, unknown: 0 },
  { day: "Wed", supported: 2, refuted: 1, unknown: 2 },
  { day: "Thu", supported: 5, refuted: 1, unknown: 1 },
  { day: "Fri", supported: 4, refuted: 3, unknown: 2 },
];

export const verifications: Verification[] = [
  {
    id: "v1",
    type: "claim",
    text: "The Great Wall of China is visible from space.",
    result: "refuted",
    confidence: 0.21,
    date: "28 May 2024",
    time: "10:30 AM",
  },
  {
    id: "v2",
    type: "question",
    text: "What causes acid rain?",
    result: "supported",
    confidence: 0.86,
    date: "27 May 2024",
    time: "10:30 AM",
  },
  {
    id: "v3",
    type: "claim",
    text: "Vitamin C prevents colds.",
    result: "not-enough-info",
    confidence: 0.48,
    date: "27 May 2024",
    time: "04:15 PM",
  },
  {
    id: "v4",
    type: "claim",
    text: "The boiling point of water is 100°C.",
    result: "supported",
    confidence: 0.93,
    date: "27 May 2024",
    time: "11:20 AM",
  },
  {
    id: "v5",
    type: "claim",
    text: "Humans use only 10% of their brain.",
    result: "refuted",
    confidence: 0.25,
    date: "26 May 2024",
    time: "09:45 PM",
  },
  {
    id: "v6",
    type: "claim",
    text: "Bats are blind.",
    result: "refuted",
    confidence: 0.13,
    date: "26 May 2024",
    time: "08:10 PM",
  },
  {
    id: "v7",
    type: "question",
    text: "How do vaccines create immunity?",
    result: "supported",
    confidence: 0.91,
    date: "25 May 2024",
    time: "02:05 PM",
  },
  {
    id: "v8",
    type: "claim",
    text: "Goldfish have a three second memory.",
    result: "refuted",
    confidence: 0.18,
    date: "24 May 2024",
    time: "06:40 PM",
  },
  {
    id: "v9",
    type: "question",
    text: "Is coffee linked to longer lifespan?",
    result: "not-enough-info",
    confidence: 0.52,
    date: "23 May 2024",
    time: "01:15 PM",
  },
];

export const exampleClaims = [
  "Is the moon made of cheese?",
  "Plants get energy from the sun.",
  "Earth is the center of the universe.",
  "Does drinking hot water burn fat?",
];

export const retrievalSources = [
  "All Sources",
  "Wikipedia",
  "Research Papers",
  "Uploaded Documents",
  "Government Sources",
  "Books",
];

export type EvidenceItem = {
  source: string;
  url: string;
  snippet: string;
};

export const answerEvidence: EvidenceItem[] = [
  {
    source: "Environmental Protection Agency (EPA)",
    url: "https://www.epa.gov/acidrain",
    snippet:
      "Acid rain results when sulfur dioxide (SO₂) and nitrogen oxides (NOₓ) are emitted into the atmosphere and transported by wind, then react with water, oxygen and other chemicals to form acidic compounds.",
  },
  {
    source: "National Aeronautics and Space Administration (NASA)",
    url: "https://climate.nasa.gov",
    snippet:
      "Satellite observations track sulfur dioxide plumes from power generation and volcanic activity, which are primary precursors of acidic deposition downwind of emission sources.",
  },
  {
    source: "Encyclopaedia Britannica",
    url: "https://www.britannica.com/science/acid-rain",
    snippet:
      "Acid rain is precipitation possessing a pH of about 5.2 or below, mainly produced from sulfur oxides and nitrogen oxides released by burning fossil fuels.",
  },
  {
    source: "World Health Organization (WHO)",
    url: "https://www.who.int",
    snippet:
      "Ambient air pollutants including SO₂ and NOₓ contribute both to acidification of ecosystems and to measurable respiratory health burdens in exposed populations.",
  },
];

export const answerDetail = {
  question: "What causes acid rain?",
  answer:
    "Acid rain is caused by the emission of sulfur dioxide (SO₂) and nitrogen oxides (NOₓ) into the atmosphere. These gases react with water vapor, oxygen, and other chemicals to form sulfuric acid and nitric acid, which then fall to the ground in wet or dry forms.",
  result: "supported" as VerificationResult,
  confidence: 0.86,
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  time: string;
  sources?: string[];
};

export const initialChat: ChatMessage[] = [
  {
    id: "m1",
    role: "user",
    text: "What causes acid rain?",
    time: "10:30 AM",
  },
  {
    id: "m2",
    role: "assistant",
    text: answerDetail.answer,
    time: "10:30 AM",
    sources: answerEvidence.map((e) => e.source),
  },
];

export type UploadedFile = {
  id: string;
  name: string;
  type: string;
  uploaded: string;
  status: "indexed" | "processing" | "failed";
  size: string;
};

export const uploads: UploadedFile[] = [
  {
    id: "u1",
    name: "research_paper.pdf",
    type: "PDF",
    uploaded: "28 May 2024",
    status: "indexed",
    size: "1.2 MB",
  },
  {
    id: "u2",
    name: "climate_report_2024.docx",
    type: "DOCX",
    uploaded: "27 May 2024",
    status: "indexed",
    size: "820 KB",
  },
  {
    id: "u3",
    name: "who_air_quality.csv",
    type: "CSV",
    uploaded: "26 May 2024",
    status: "processing",
    size: "310 KB",
  },
  {
    id: "u4",
    name: "lecture_notes.txt",
    type: "TXT",
    uploaded: "24 May 2024",
    status: "failed",
    size: "48 KB",
  },
];

export const sourceLibrary = [
  {
    id: "wikipedia",
    title: "Wikipedia",
    snippet:
      "Community-curated encyclopedic entries used for broad background context and entity disambiguation.",
    relevance: 0.82,
    documents: 1240,
  },
  {
    id: "papers",
    title: "Research Papers",
    snippet:
      "Peer-reviewed articles from open-access repositories, prioritised for scientific and medical claims.",
    relevance: 0.94,
    documents: 587,
  },
  {
    id: "uploads",
    title: "Uploaded Documents",
    snippet:
      "Your own PDFs, reports and datasets, chunked and embedded so answers can cite your private evidence.",
    relevance: 0.76,
    documents: 24,
  },
  {
    id: "gov",
    title: "Government Sources",
    snippet:
      "Official agency publications such as EPA, NASA and WHO, used as high-trust references for policy claims.",
    relevance: 0.89,
    documents: 316,
  },
  {
    id: "books",
    title: "Books",
    snippet:
      "Reference texts and textbooks providing stable definitions and historical grounding for established facts.",
    relevance: 0.71,
    documents: 152,
  },
];

export type GraphEntity = {
  id: string;
  label: string;
  kind: string;
  description: string;
  relations: string[];
};

export const graphEntities: Record<string, GraphEntity> = {
  acid_rain: {
    id: "acid_rain",
    label: "Acid Rain",
    kind: "Phenomenon",
    description:
      "Precipitation with a pH below ~5.2, formed when atmospheric sulfur and nitrogen oxides react with water vapour.",
    relations: ["caused by Sulfur Dioxide", "caused by Nitrogen Oxides", "damages Forests"],
  },
  so2: {
    id: "so2",
    label: "Sulfur Dioxide",
    kind: "Compound",
    description:
      "A colourless gas released mainly by fossil-fuel combustion and volcanic activity; a primary acid rain precursor.",
    relations: ["emitted by Power Plants", "forms Sulfuric Acid"],
  },
  nox: {
    id: "nox",
    label: "Nitrogen Oxides",
    kind: "Compound",
    description:
      "Reactive gases produced by high-temperature combustion, contributing to acid deposition and smog.",
    relations: ["emitted by Vehicles", "forms Nitric Acid"],
  },
  power_plants: {
    id: "power_plants",
    label: "Power Plants",
    kind: "Source",
    description: "Coal and oil fired generation facilities responsible for a majority of SO₂ emissions.",
    relations: ["emits Sulfur Dioxide"],
  },
  vehicles: {
    id: "vehicles",
    label: "Vehicles",
    kind: "Source",
    description: "Internal combustion engines emitting nitrogen oxides during fuel combustion.",
    relations: ["emits Nitrogen Oxides"],
  },
  sulfuric: {
    id: "sulfuric",
    label: "Sulfuric Acid",
    kind: "Compound",
    description: "Strong acid formed when SO₂ oxidises and dissolves in atmospheric water.",
    relations: ["component of Acid Rain"],
  },
  nitric: {
    id: "nitric",
    label: "Nitric Acid",
    kind: "Compound",
    description: "Acid formed from nitrogen oxides reacting with water vapour and oxidants.",
    relations: ["component of Acid Rain"],
  },
  forests: {
    id: "forests",
    label: "Forests & Lakes",
    kind: "Impact",
    description: "Ecosystems acidified by deposition, leading to nutrient leaching and aquatic species loss.",
    relations: ["damaged by Acid Rain"],
  },
  epa: {
    id: "epa",
    label: "EPA",
    kind: "Source Authority",
    description: "US Environmental Protection Agency — high-trust reference for acid rain evidence.",
    relations: ["documents Acid Rain"],
  },
};
