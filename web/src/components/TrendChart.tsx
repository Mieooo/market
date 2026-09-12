import * as echarts from "echarts/core";
import { GridComponent, TooltipComponent } from "echarts/components";
import { LineChart } from "echarts/charts";
import { SVGRenderer } from "echarts/renderers";
import { useEffect, useRef } from "react";
echarts.use([GridComponent,TooltipComponent,LineChart,SVGRenderer]);

interface Series{name:string;color:string;values:number[]}
export function TrendChart({series,height=270}:{series:Series[];height?:number}){
  const ref=useRef<HTMLDivElement>(null);
  useEffect(()=>{if(!ref.current)return;const chart=echarts.init(ref.current,undefined,{renderer:"svg"});chart.setOption({animationDuration:650,grid:{left:8,right:8,top:18,bottom:26,containLabel:true},tooltip:{trigger:"axis",backgroundColor:"#ffffff",borderColor:"rgba(0,0,0,.12)",extraCssText:"box-shadow:0 12px 30px rgba(0,0,0,.10);border-radius:8px",textStyle:{color:"#171717",fontSize:12},axisPointer:{lineStyle:{color:"rgba(0,0,0,.18)"}}},xAxis:{type:"category",boundaryGap:false,data:["W26","W27","W28","W29","W30","W31","W32","W33","W34","W35","W36","W37"],axisLine:{lineStyle:{color:"rgba(0,0,0,.12)"}},axisTick:{show:false},axisLabel:{color:"#737373",fontSize:10,interval:1}},yAxis:{type:"value",min:0,max:100,splitNumber:4,axisLabel:{color:"#737373",fontSize:10},splitLine:{lineStyle:{color:"rgba(0,0,0,.07)"}}},series:series.map(item=>({name:item.name,type:"line",data:item.values,smooth:.34,symbol:"none",lineStyle:{color:item.color,width:2.2},itemStyle:{color:item.color},areaStyle:series.length===1?{color:{type:"linear",x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:`${item.color}32`},{offset:1,color:`${item.color}00`}]}}:undefined,emphasis:{focus:"series"}}))});const resize=()=>chart.resize();window.addEventListener("resize",resize);return()=>{window.removeEventListener("resize",resize);chart.dispose();}},[series]);
  return <div className="trend-chart" ref={ref} style={{height}} role="img" aria-label={`${series.map(s=>s.name).join("、")}最近十二周趋势图`}/>;
}
