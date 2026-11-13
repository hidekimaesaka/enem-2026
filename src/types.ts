export type Area = 'matematica' | 'biologia' | 'fisica' | 'quimica';
export type Question = {id:string;year:number;index:number;area:Area;topics:string[];context:string;alternativesIntroduction:string;alternatives:{letter:string;text:string|null;file:string|null}[];correctAlternative:string;explanation:string[];rubric:[number,number,number];rationale:string;source:string};
export type Answer = {letter:string;date:string;elapsedMs?:number};
export type Answers = Record<string,Answer>;
