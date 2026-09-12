import { describe,expect,it } from "vitest";
import { evidenceRecords,problems } from "../mockData";
import { MockRadarRepository } from "./RadarRepository";

describe("mock radar data",()=>{
  it("keeps the promised MVP sample shape",()=>{
    expect(problems).toHaveLength(10);
    expect(evidenceRecords).toHaveLength(50);
    expect(evidenceRecords.filter(item=>item.status==="verified")).toHaveLength(40);
  });
  it("filters problems without a front-end enum",async()=>{
    const repository=new MockRadarRepository();
    const results=await repository.getProblems({industry:"制造"});
    expect(results.map(item=>item.id)).toContain("industry-workflows");
    expect(results.every(item=>item.industries.includes("制造"))).toBe(true);
  });
  it("keeps unverified leads out of the verified evidence set",async()=>{
    const repository=new MockRadarRepository();
    const results=await repository.getEvidence({status:"verified"});
    expect(results).toHaveLength(40);
    expect(results.every(item=>item.status==="verified")).toBe(true);
  });
});
