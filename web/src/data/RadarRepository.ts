import { evidenceStatusSchema, evidenceRecords, overview, problems, signals, sourceTypeSchema, trendStateSchema, type Evidence, type Problem, type Signal, type SourceType, type TrendState } from "../mockData";

export interface ProblemQuery { q?:string; state?:TrendState|""; industry?:string; }
export interface EvidenceQuery { q?:string; type?:SourceType|""; status?:"verified"|"lead_only"|"failed"|""; problemId?:string; }
export interface SignalQuery { type?:SourceType|""; }
export interface RadarRepository { getOverview():Promise<typeof overview>; getProblems(query?:ProblemQuery):Promise<Problem[]>; getProblem(id:string):Promise<Problem|undefined>; getEvidence(query?:EvidenceQuery):Promise<Evidence[]>; getSignals(query?:SignalQuery):Promise<Signal[]>; }
const scenario=()=>new URLSearchParams(globalThis.location?.search??"").get("scenario")??"default";
const delay=(ms=100)=>new Promise(resolve=>setTimeout(resolve,scenario()==="loading"?1200:ms));
const failIfRequested=()=>{if(scenario()==="error")throw new Error("Mock error scenario")};

export class MockRadarRepository implements RadarRepository {
  async getOverview(){await delay();failIfRequested();return {...overview,isStale:scenario()==="stale"};}
  async getProblems(query:ProblemQuery={}){await delay();failIfRequested();if(scenario()==="empty")return[];const state=query.state?trendStateSchema.parse(query.state):"";const term=query.q?.trim().toLowerCase()??"";const result=problems.filter(p=>(!state||p.state===state)&&(!query.industry||p.industries.includes(query.industry))&&(!term||JSON.stringify(p).toLowerCase().includes(term)));return scenario()==="partial"?result.slice(0,6):result;}
  async getProblem(id:string){await delay(60);failIfRequested();return problems.find(p=>p.id===id);}
  async getEvidence(query:EvidenceQuery={}){await delay();failIfRequested();if(scenario()==="empty")return[];const type=query.type?sourceTypeSchema.parse(query.type):"";const status=query.status?evidenceStatusSchema.parse(query.status):"";const term=query.q?.trim().toLowerCase()??"";const result=evidenceRecords.filter(e=>(!type||e.type===type)&&(!status||e.status===status)&&(!query.problemId||e.problemId===query.problemId)&&(!term||JSON.stringify(e).toLowerCase().includes(term)));return scenario()==="partial"?result.slice(0,24):result;}
  async getSignals(query:SignalQuery={}){await delay();failIfRequested();if(scenario()==="empty")return[];const result=signals.filter(s=>!query.type||s.type===query.type);return scenario()==="partial"?result.slice(0,9):result;}
}
export class ApiRadarRepository implements RadarRepository {
  private async get<T>(path:string):Promise<T>{const response=await fetch(`/api/v1${path}`);if(!response.ok)throw new Error(`API ${response.status}`);const payload=await response.json();return payload.data??payload;}
  getOverview(){return this.get<typeof overview>("/overview");} getProblems(){return this.get<Problem[]>("/problems");} getProblem(id:string){return this.get<Problem>(`/problems/${id}`);} getEvidence(){return this.get<Evidence[]>("/evidence");} getSignals(){return this.get<Signal[]>("/signals");}
}
export const radarRepository:RadarRepository=import.meta.env.VITE_DATA_MODE==="api"?new ApiRadarRepository():new MockRadarRepository();
