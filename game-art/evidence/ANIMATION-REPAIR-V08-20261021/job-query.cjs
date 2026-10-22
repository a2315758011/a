'use strict';
async function queryExistingJob({jobId,sourceProjectId,sourceTaskId,endpoints,fetchImpl=fetch,timeoutMs=3000}){
 const failures=[];const seen=new Set();
 for(const endpoint of endpoints.filter(Boolean)){
  if(seen.has(endpoint.baseUrl))continue;seen.add(endpoint.baseUrl);
  const u=new URL(endpoint.baseUrl);if(!['127.0.0.1','localhost','[::1]'].includes(u.hostname))throw Error('Gateway must remain loopback');
  try{
   const res=await fetchImpl(endpoint.baseUrl+'/v1/jobs/'+encodeURIComponent(jobId),{method:'GET',headers:endpoint.headers,signal:AbortSignal.timeout(timeoutMs)});
   if(!res.ok){failures.push({baseUrl:endpoint.baseUrl,status:res.status});continue;}
   const body=await res.json(),j=body.job;
   if(j?.id!==jobId||j.sourceProjectId!==sourceProjectId||j.sourceTaskId!==sourceTaskId){failures.push({baseUrl:endpoint.baseUrl,error:'JOB_IDENTITY_MISMATCH'});continue;}
   return {job:j,baseUrl:endpoint.baseUrl,recoveredFromOriginal:failures.length>0,failures};
  }catch(e){failures.push({baseUrl:endpoint.baseUrl,error:e.message});}
 }
 // Re-query the persistent original subtask; a missing in-memory job is never permission to POST again.
 for(const endpoint of endpoints.filter(Boolean)){
  try{
   const res=await fetchImpl(endpoint.baseUrl+'/v1/orchestrator/tasks/gateway-'+encodeURIComponent(jobId)+'/subtasks',{method:'GET',headers:endpoint.headers,signal:AbortSignal.timeout(timeoutMs)});
   if(!res.ok)continue;const body=await res.json();const t=body.subtasks?.find(t=>t.id===jobId&&t.input?.businessContext?.sourceProjectId===sourceProjectId&&t.input?.businessContext?.sourceTaskId===sourceTaskId);
   if(t)return {job:{id:jobId,status:t.status,sourceProjectId,sourceTaskId,result:t.result,error:t.error,artifacts:t.result?.artifacts||[],singleSubmitLocked:t.singleSubmitLocked,submittedAt:t.submittedAt,conversationId:t.conversationId},baseUrl:endpoint.baseUrl,persistentSubtask:true,failures};
  }catch(e){failures.push({baseUrl:endpoint.baseUrl,error:e.message});}
 }
 const e=Error('Original job cannot be reconciled; retained without resubmission');e.code='ORIGINAL_JOB_UNAVAILABLE_NO_RESUBMIT';e.failures=failures;throw e;
}
module.exports={queryExistingJob};