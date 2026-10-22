// "Ask this guide" stream (CONTRACT §4b).
export interface AskCitation {
  marker: string;
  label: "DOCS" | "TESTED" | "COMMUNITY" | "UNCERTAIN";
  source_id: string | null;
  url: string | null;
  title: string | null;
  quote: string | null;
  found_in: "visible" | "hidden_section" | null;
  fact: string;
}
export interface AskAction {
  kind: "set_situation";
  question_id: string;
  option_id: string;
  label: string;
}
export interface AskAnswerMeta {
  covered: boolean;
  suggest: null | "regenerate";
}
