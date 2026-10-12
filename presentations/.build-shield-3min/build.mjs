import fs from 'node:fs/promises';
import { constants as fsConstants } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const workspaceDir = 'D:/SCHOLARSHIPS/My Items/Degree Project/FYP/SHIELD';
const skillDir = 'C:/Users/User/.codex/plugins/cache/openai-primary-runtime/presentations/26.1011.11113/skills/presentations';
const modulesDir = 'C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const pythonExecutable = 'C:/Users/User/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
process.env.RUNTIME_NODE_MODULES = modulesDir;
const { Presentation, PresentationFile, FileBlob } = await import(pathToFileURL(path.join(modulesDir, '@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const { finalizePresentation, resolvePresentationFont } = await import(pathToFileURL(path.join(skillDir, 'container_tools/artifact_tool_utils.mjs')).href);
const buildDir = path.join(workspaceDir, 'presentations/.build-shield-3min');
const outputDir = path.join(workspaceDir, 'presentations/output');
const fontFamily = resolvePresentationFont({fontFamily:'Arial'});
const sections = [
  {
    time:'0:00–0:30', cue:'The business owner',
    text:'Imagine you run a small bakery. Every morning, you open the doors, serve your customers, and hope the business keeps growing. Now you need a loan to buy a new oven. You bring your financial records to the bank. Behind those numbers are your savings, your staff, and your plans for the future. How can the bank understand the financial risk behind your application?'
  },
  {
    time:'0:30–1:00', cue:'The research question',
    text:'That question led to my final year project, SHIELD: SME Health Indicator and Evaluator for Loan Decisions. My research asks whether machine learning can help assess bankruptcy risk while making its predictions understandable. A missed warning can expose the bank to losses. A false alarm can make a viable business look risky. Both mistakes matter, so a useful system needs careful evaluation.'
  },
  {
    time:'1:00–1:40', cue:'Financial records and risk estimate',
    text:'I worked with historical company financial data and used Information Gain to select twenty financial indicators. It ranks indicators by how much information they provide about bankruptcy. These include profitability and borrowing measures. I then trained a Random Forest model, which combines the decisions of many decision trees to produce a risk estimate. Bankruptcy cases are relatively rare in the data, so I also investigated balancing the training examples and adjusting the point at which the model raises a warning.'
  },
  {
    time:'1:40–2:10', cue:'Reasons behind the estimate',
    text:'But a risk number alone leaves the loan officer asking, why? SHIELD uses an explanation method called SHAP to highlight which financial indicators push the model’s estimate up or down. The web prototype presents that estimate alongside the explanation. For our bakery owner, this gives the officer specific financial signals to investigate and discuss, while the officer remains responsible for the lending decision.'
  },
  {
    time:'2:10–2:45', cue:'The finding and its trade-off',
    text:'In one exploratory experiment, the model flagged thirty-five of forty-four bankrupt companies. It also flagged eighty-six companies that were not bankrupt. That shows the trade-off: catching more warning signs can bring more false alarms. Because the evaluation data had already been reused during development, these findings are preliminary. Further testing on fresh data, including data relevant to Malaysian SMEs, is needed before practical use.'
  },
  {
    time:'2:45–3:00', cue:'The human purpose',
    text:'My aim is to help loan officers make more informed decisions, with financial evidence they can question and understand. For a business owner asking for that new oven, the decision should come with reasons. Thank you.'
  }
];
await fs.writeFile(path.join(buildDir,'speech.json'), JSON.stringify(sections,null,2));
const count = sections.reduce((n,s)=>n+s.text.split(/\s+/).length,0);
console.log(JSON.stringify({spokenWordCount:count,approxMinutesAt135Wpm:count/135}));

const presentation = Presentation.create({slideSize:{width:1280,height:720}});
const slide = presentation.slides.add();
slide.background.fill = '#F8F5EF';
const ink = '#242A2C', muted = '#575C5B', gold = '#A87513';
function text(name, value, x,y,w,h,size,bold=false,color=ink){
  const shape=slide.shapes.add({geometry:'textbox',name,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0,style:'solid'}});
  shape.text=value;
  shape.text.style={typeface:fontFamily,fontSize:size,bold,color,alignment:'left',verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0};
  return shape;
}
text('project-title','SHIELD',64,47,570,100,84,true);
text('research-title','Understanding financial risk\nbefore a loan decision',67,160,570,112,40,true);
text('input-heading','Financial records',68,306,510,38,29,true);
text('input-detail','20 indicators selected with Information Gain',68,347,548,36,24,false,muted);
text('prediction-heading','Risk estimate',68,406,510,38,29,true);
text('prediction-detail','Random Forest prediction',68,447,520,36,24,false,muted);
text('explanation-heading','Reasons behind the estimate',68,506,540,40,29,true);
text('explanation-detail','SHAP explanations for human review',68,547,560,36,24,false,muted);

const imageBytes=new Uint8Array(await fs.readFile(path.join(buildDir,'business-owner.png')));
slide.images.add({blob:imageBytes,contentType:'image/png',alt:'Illustration of a fictional small-business owner holding financial records in a bakery.',fit:'contain',position:{left:650,top:64,width:590,height:393}});
text('finding-count','35 of 44',681,478,480,71,57,true,gold);
text('finding-description','bankrupt companies flagged',682,551,500,36,26,true);
text('false-alarms','86 non-bankrupt companies also flagged',682,599,534,35,23,false,muted);
text('result-caveat','Exploratory evaluation. Further validation needed.',68,654,1150,38,23,false,muted);

const sourceNotes = [
  'SOURCES AND INTERPRETATION',
  'Project identity and prototype: README.md and UPDATE.md in the SHIELD workspace. Random Forest and SHAP implementation confirmed in backend/main.py.',
  'Exploratory experiment: reports/focused_improvement/ba8ead7ba47c9dce/holdout_results.csv, row RF_SMOTE025_LEAF3 / Frozen OOF threshold 0.27969295288128426. TP=35, FN=9, FP=86, TN=1234. Bankrupt-class recall=35/44=79.545%; precision=35/121=28.926%. These are results of an exploratory research candidate, not a claim about the deployed prototype.',
  'frozen_choice.json and run_config.json label the holdout as historically reused and exploratory. Do not call it independent test evidence or validated Malaysian SME performance. Current project documentation names a foreign bankruptcy dataset; geographic origin was not independently verified for this presentation.',
  'The bakery owner is an imagined scenario. No claim is made that SHIELD has assessed a real bakery, improved lending outcomes, or demonstrated future-warning lead time.',
  'Financial records are twenty selected indicators in the IG20 experiment. SHAP explains model contributions, not causal relationships.',
  'Illustration: generated with the built-in ImageGen tool for this presentation. Fictional person and business. Asset: presentations/.build-shield-3min/business-owner.png.'
].join('\n\n');
slide.speakerNotes.text=sections.map(s=>`${s.time} — ${s.cue}\n${s.text}`).join('\n\n')+'\n\n'+sourceNotes;

const script = '# SHIELD: Three-minute storytelling script\n\n'+
  'Keep the same static slide on screen throughout. The timings are rehearsal targets, not automatic slide changes. Read only the spoken paragraphs below.\n\n'+
  sections.map(s=>`## ${s.time} — ${s.cue}\n\n${s.text}`).join('\n\n')+
  '\n\n## Rehearsal notes\n\n'+
  `The script contains ${count} spoken words. Aim for around 130–135 words per minute, with brief pauses. Rehearse with a timer: individual delivery speed varies. Finish comfortably before three minutes.\n\n`+
  '- Pause after the opening question and let the audience picture the bakery.\n'+
  '- Say “SHIELD” like the ordinary word. Say “SHAP” like “shap”.\n'+
  '- Emphasise “thirty-five of forty-four”, then give the false-alarm figure equal clarity.\n'+
  '- Use the slide as a memory aid: financial records, risk estimate, explanation, then the finding. Keep eye contact during the closing.\n'+
  '- Check the event rules for slide count, aspect ratio and presenter identification before submission. This file uses one static 16:9 slide with no animations.\n\n'+
  '## Optional cut if your rehearsal runs long\n\n'+
  'Omit “These include profitability and borrowing measures.” and “The web prototype presents that estimate alongside the explanation.” Keep the research limitation and false-alarm figure.\n\n'+
  '## Evidence behind the result\n\n'+sourceNotes+'\n';
await fs.writeFile(path.join(outputDir,'SHIELD_3_Minute_Script.md'),script,'utf8');
await fs.writeFile(path.join(buildDir,'slide.layout.json'),await (await slide.export({format:'layout'})).text());
await fs.writeFile(path.join(buildDir,'draft.png'),new Uint8Array(await (await presentation.export({slide,format:'png',scale:1.5})).arrayBuffer()));
const candidatePath=path.join(buildDir,'candidate.pptx');
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const finalPath=path.join(outputDir,'SHIELD_3_Minute_Story.pptx');
// Publish exclusively by copy when this Windows workspace does not support hard links.
// All finalizer validation and before/after byte-hash checks remain in place.
const originalLink=fs.link.bind(fs);
fs.link=async (source,destination)=>{
  try { return await originalLink(source,destination); }
  catch(error){
    if(error.code!=='EPERM' || path.resolve(destination)!==path.resolve(finalPath) || path.dirname(source)!==path.dirname(finalPath) || !source.endsWith('.validated')) throw error;
    return await fs.copyFile(source,destination,fsConstants.COPYFILE_EXCL);
  }
};
const finalization=await finalizePresentation({workspaceDir,candidatePath,finalPath,pythonExecutable,
  integrityValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_layout_geometry.py'),
  explicitTotalSlideCount:1,
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],
  requiredNativeTableOwnerSlides:[], requiredNativeChartOwnerSlides:[],
  fontPolicy:{basis:'design',families:[fontFamily]},verifyArtifactToolImport:true,
  receiptPath:path.join(buildDir,'validation.json')
});
console.log(JSON.stringify({finalization}));
const finalDeck=await PresentationFile.importPptx(await FileBlob.load(finalPath));
await fs.writeFile(path.join(outputDir,'SHIELD_3_Minute_Slide.png'),new Uint8Array(await (await finalDeck.export({slide:finalDeck.slides.items[0],format:'png',scale:1.5})).arrayBuffer()));
console.log(JSON.stringify({finalPath,scriptPath:path.join(outputDir,'SHIELD_3_Minute_Script.md')}));
