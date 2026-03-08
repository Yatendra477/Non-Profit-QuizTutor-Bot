"""
webapp.py — Flask Web UI for the Non-Profit Quiz/Tutor Bot.

Run with:  python webapp.py
Then open: http://localhost:5000
"""
import json
import os
import random
from flask import Flask, render_template_string, request, jsonify, session

import config

app = Flask(__name__)
app.secret_key = "nonprofit-quiz-secret-2026"

# ── Inline HTML template ──────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Non-Profit Quiz/Tutor Bot</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet"/>
<style>
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:'Inter',sans-serif;background:#f1f5f9;color:#1e293b;min-height:100vh;}
/* Layout */
.shell{display:flex;min-height:100vh;}
.sidebar{width:240px;background:#0f172a;color:#e2e8f0;padding:28px 16px;flex-shrink:0;display:flex;flex-direction:column;gap:8px;}
.sidebar h2{font-size:18px;font-weight:700;color:#fff;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #1e3a5f;}
.sidebar h2 span{margin-right:8px;}
.nav-btn{width:100%;padding:10px 14px;border:none;border-radius:8px;background:transparent;color:#94a3b8;font-size:13px;font-weight:500;text-align:left;cursor:pointer;transition:.2s;}
.nav-btn:hover,.nav-btn.active{background:#1e3a5f;color:#fff;}
.sidebar-footer{margin-top:auto;font-size:11px;color:#475569;line-height:1.6;}
.main{flex:1;padding:36px 40px;max-width:860px;}
/* Cards */
.card{background:#fff;border-radius:12px;padding:24px 28px;margin:14px 0;box-shadow:0 1px 4px rgba(0,0,0,.06);border:1px solid #e5e7eb;}
.card-blue{border-left:4px solid #3b82f6;}
.card-green{border-left:4px solid #10b981;}
.card-yellow{border-left:4px solid #f59e0b;}
.card-red{border-left:4px solid #ef4444;}
.card-purple{border-left:4px solid #8b5cf6;}
h1{font-size:26px;font-weight:700;margin-bottom:6px;}
h2{font-size:19px;font-weight:700;margin-bottom:14px;}
h3{font-size:15px;font-weight:700;margin-bottom:8px;}
p{color:#475569;line-height:1.7;margin-bottom:10px;}
/* Buttons */
.btn{display:inline-block;padding:10px 22px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;border:none;transition:.2s;}
.btn-primary{background:#0f4c81;color:#fff;}
.btn-primary:hover{background:#0c3d6b;}
.btn-secondary{background:#e5e7eb;color:#374151;}
.btn-secondary:hover{background:#d1d5db;}
.btn-sm{padding:7px 16px;font-size:12px;}
.btn-row{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap;}
/* Home grid */
.home-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:20px 0;}
.home-card{border-radius:12px;padding:24px;cursor:pointer;transition:.15s;border:2px solid transparent;}
.home-card:hover{border-color:#3b82f6;transform:translateY(-2px);}
.home-card .icon{font-size:32px;margin-bottom:12px;}
.home-card h3{font-size:16px;font-weight:700;margin-bottom:6px;}
/* Quiz */
.question-hdr{background:#0f172a;color:#fff;border-radius:10px;padding:14px 20px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;font-size:13px;}
.progress-bar{background:#1e3a5f;border-radius:4px;height:4px;margin-bottom:18px;}
.progress-fill{background:#3b82f6;height:4px;border-radius:4px;transition:.4s;}
.option-label{display:block;padding:12px 16px;border:2px solid #e5e7eb;border-radius:8px;margin-bottom:8px;cursor:pointer;transition:.15s;font-size:13.5px;}
.option-label:hover{border-color:#3b82f6;background:#eff6ff;}
.option-label input{margin-right:10px;}
.option-label.correct-opt{border-color:#10b981;background:#f0fdf4;}
.option-label.wrong-opt{border-color:#ef4444;background:#fff1f2;}
textarea{width:100%;padding:12px 14px;border:2px solid #e5e7eb;border-radius:8px;font-size:13.5px;font-family:inherit;resize:vertical;transition:.15s;}
textarea:focus{outline:none;border-color:#3b82f6;}
/* Feedback */
.feedback-box{border-radius:10px;padding:16px 20px;margin:14px 0;}
.feedback-correct{background:#f0fdf4;border:1px solid #86efac;}
.feedback-wrong{background:#fff1f2;border:1px solid #fca5a5;}
/* Score */
.score-big{font-size:52px;font-weight:800;text-align:center;color:#0f4c81;margin:16px 0;}
/* Table */
table{width:100%;border-collapse:collapse;font-size:13px;margin:14px 0;}
th{background:#0f172a;color:#fff;padding:10px 12px;text-align:left;}
td{padding:9px 12px;border-bottom:1px solid #f0f0f0;}
tr:nth-child(even) td{background:#f8fafc;}
/* Scenario box */
.scenario-box{background:#eff6ff;border-left:4px solid #3b82f6;border-radius:0 8px 8px 0;padding:16px 18px;margin:16px 0;font-size:13.5px;line-height:1.7;color:#1e3a5f;}
/* Badge */
.badge{display:inline-block;padding:3px 12px;border-radius:12px;font-size:11px;font-weight:700;}
.badge-green{background:#dcfce7;color:#166534;}
.badge-red{background:#fee2e2;color:#991b1b;}
/* Select */
select{width:100%;padding:10px 14px;border:2px solid #e5e7eb;border-radius:8px;font-size:13.5px;font-family:inherit;background:#fff;}
select:focus{outline:none;border-color:#3b82f6;}
.info-strip{background:#dbeafe;border-radius:8px;padding:12px 16px;font-size:12.5px;color:#1e40af;margin:12px 0;}
.spinner{display:inline-block;width:18px;height:18px;border:3px solid #e5e7eb;border-top:3px solid #0f4c81;border-radius:50%;animation:spin .8s linear infinite;vertical-align:middle;margin-right:8px;}
@keyframes spin{to{transform:rotate(360deg)}}
.hidden{display:none!important;}
/* hint */
.hint-toggle{color:#3b82f6;font-size:12px;cursor:pointer;text-decoration:underline;margin-bottom:10px;display:inline-block;}
.hint-box{background:#fef9c3;border:1px solid #fde047;border-radius:6px;padding:10px 14px;font-size:12.5px;color:#854d0e;margin-bottom:10px;}
/* info grid */
.info-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0;}
.info-item{background:#fff;border-radius:10px;padding:14px;text-align:center;border:1px solid #e5e7eb;}
.info-item .num{font-size:26px;font-weight:800;color:#0f4c81;line-height:1;}
.info-item .lbl{font-size:11px;color:#6b7280;margin-top:4px;}
</style>
</head>
<body>
<div class="shell">

<!-- SIDEBAR -->
<div class="sidebar">
  <h2><span>🎓</span>Non-Profit Bot</h2>
  <button class="nav-btn" onclick="showPage('home')">🏠 Home</button>
  <button class="nav-btn" onclick="showPage('quiz-setup')">📝 Quiz Mode</button>
  <button class="nav-btn" onclick="showPage('tutor-setup')">✍️ Writing Tutor</button>
  <div class="sidebar-footer">
    Powered by<br>Google Gemini + ChromaDB<br>LangChain · Flask · Python
  </div>
</div>

<!-- MAIN -->
<div class="main">

<!-- ════ HOME ════ -->
<div id="page-home">
  <h1>🎓 Non-Profit Quiz / Tutor Bot</h1>
  <p style="font-size:15px;">An AI-powered educational assistant for non-profit donor communication — built with RAG + LLM</p>
  <div class="home-grid">
    <div class="card home-card" onclick="showPage('quiz-setup')">
      <div class="icon">📝</div>
      <h3>Quiz Mode</h3>
      <p>Answer AI-generated questions on donor email topics. Get RAG-powered explanations for wrong answers.</p>
    </div>
    <div class="card home-card" onclick="showPage('tutor-setup')">
      <div class="icon">✍️</div>
      <h3>Writing Tutor</h3>
      <p>Draft a donor email for a real-world scenario. Receive scored AI feedback: strengths, improvements, expert rewrite.</p>
    </div>
  </div>
  <div class="info-grid">
    <div class="info-item"><div class="num">15</div><div class="lbl">Donor Emails in KB</div></div>
    <div class="info-item"><div class="num">80+</div><div class="lbl">Vector Chunks</div></div>
    <div class="info-item"><div class="num">3</div><div class="lbl">Question Types</div></div>
    <div class="info-item"><div class="num">6</div><div class="lbl">Writing Scenarios</div></div>
  </div>
  <div class="info-strip">🔗 How it works: Donor emails are embedded into ChromaDB → Gemini retrieves relevant chunks (RAG) → Generates questions / evaluates your email → Returns grounded, factual feedback.</div>
</div>

<!-- ════ QUIZ SETUP ════ -->
<div id="page-quiz-setup" class="hidden">
  <h1>📝 Quiz Mode</h1>
  <p>Configure your quiz session below.</p>
  <div class="card">
    <h3>Number of Questions</h3>
    <input id="num-q" type="range" min="1" max="10" value="5" oninput="document.getElementById('num-q-val').textContent=this.value" style="width:100%;margin:10px 0;"/>
    <p>Questions: <strong id="num-q-val">5</strong></p>
  </div>
  <div class="card card-blue">
    <p>Mix of Multiple Choice, True/False, and Short Answer questions — generated fresh from the donor email knowledge base using Gemini AI.</p>
  </div>
  <div class="btn-row">
    <button class="btn btn-primary" onclick="startQuiz()"><span id="quiz-gen-spinner" class="spinner hidden"></span>🚀 Generate &amp; Start Quiz</button>
    <button class="btn btn-secondary" onclick="showPage('home')">← Back</button>
  </div>
  <div id="quiz-setup-error" class="hidden" style="margin-top:14px;color:#ef4444;font-size:13px;"></div>
</div>

<!-- ════ QUIZ QUESTION ════ -->
<div id="page-quiz-question" class="hidden">
  <div class="progress-bar"><div class="progress-fill" id="q-progress" style="width:0%"></div></div>
  <div class="question-hdr">
    <span id="q-counter">Q1 of 5</span>
    <span id="q-meta">Topic · Difficulty</span>
  </div>
  <h2 id="q-text">Question text here</h2>

  <!-- MCQ / TF options -->
  <div id="q-options"></div>

  <!-- Short answer -->
  <div id="q-shortanswer" class="hidden">
    <textarea id="sa-input" rows="4" placeholder="Type your answer here..."></textarea>
  </div>

  <div id="q-hint-toggle-row">
    <span class="hint-toggle" onclick="toggleHint()">💡 Show hint</span>
  </div>
  <div id="q-hint" class="hint-box hidden"></div>

  <div class="btn-row">
    <button id="q-submit-btn" class="btn btn-primary" onclick="submitAnswer()"><span id="q-spinner" class="spinner hidden"></span>Submit Answer</button>
  </div>

  <!-- Feedback (hidden until submitted) -->
  <div id="q-feedback" class="hidden" style="margin-top:20px;">
    <div id="q-feedback-box" class="feedback-box"></div>
    <div id="q-explanation" class="card" style="margin-top:12px;"></div>
    <div id="q-sources" style="font-size:12px;color:#9ca3af;margin-top:6px;"></div>
    <div class="btn-row">
      <button id="q-next-btn" class="btn btn-primary" onclick="nextQuestion()">Next Question →</button>
      <button id="q-finish-btn" class="btn btn-primary hidden" onclick="showResults()">🏁 See Results</button>
    </div>
  </div>
</div>

<!-- ════ QUIZ RESULTS ════ -->
<div id="page-quiz-results" class="hidden">
  <h1>🏁 Quiz Results</h1>
  <div class="score-big" id="results-score">0/0</div>
  <div id="results-grade" class="card" style="text-align:center;"></div>
  <br/>
  <h2>Answer Review</h2>
  <table>
    <thead><tr><th>#</th><th>Question</th><th>Result</th><th>Topic</th></tr></thead>
    <tbody id="results-table"></tbody>
  </table>
  <div id="results-weak" style="margin-top:16px;"></div>
  <div class="btn-row">
    <button class="btn btn-primary" onclick="showPage('quiz-setup')">🔁 Take Another Quiz</button>
    <button class="btn btn-secondary" onclick="showPage('tutor-setup')">✍️ Try Writing Tutor</button>
  </div>
</div>

<!-- ════ TUTOR SETUP ════ -->
<div id="page-tutor-setup" class="hidden">
  <h1>✍️ Writing Tutor</h1>
  <p>Choose a real-world non-profit email scenario and draft your best response.</p>
  <div class="card">
    <h3>Select Scenario</h3>
    <select id="scenario-select" onchange="updateScenarioPreview()">
      <option value="random">🎲 Random scenario</option>
      <option value="0">1. First-Time Donor Thank-You</option>
      <option value="1">2. Year-End Matching Gift Appeal</option>
      <option value="2">3. Lapsed Donor Re-Engagement</option>
      <option value="3">4. Volunteer Appreciation &amp; Recruitment</option>
      <option value="4">5. Grant Reporting Reminder</option>
      <option value="5">6. Planned Giving Introduction</option>
    </select>
    <div id="scenario-preview" class="scenario-box" style="margin-top:14px;">Select a scenario to see its description.</div>
  </div>
  <div class="btn-row">
    <button class="btn btn-primary" onclick="startTutor()">Use This Scenario →</button>
    <button class="btn btn-secondary" onclick="showPage('home')">← Back</button>
  </div>
</div>

<!-- ════ TUTOR DRAFT ════ -->
<div id="page-tutor-draft" class="hidden">
  <h1>✍️ Write Your Email</h1>
  <div id="tutor-scenario-display" class="scenario-box"></div>
  <div class="card">
    <h3>Your Email Draft</h3>
    <textarea id="tutor-draft" rows="12" placeholder="Subject: ...\n\nDear [Name],\n\n[Your email body here]\n\nBest regards,\n[Your name]"></textarea>
  </div>
  <div class="btn-row">
    <button class="btn btn-primary" onclick="submitDraft()"><span id="tutor-spinner" class="spinner hidden"></span>📤 Submit for Evaluation</button>
    <button class="btn btn-secondary" onclick="showPage('tutor-setup')">← Change Scenario</button>
  </div>
  <div id="tutor-draft-error" class="hidden" style="margin-top:14px;color:#ef4444;font-size:13px;"></div>
</div>

<!-- ════ TUTOR FEEDBACK ════ -->
<div id="page-tutor-feedback" class="hidden">
  <h1>📊 Writing Feedback</h1>
  <div id="tutor-score-box" class="card" style="text-align:center;font-size:22px;font-weight:700;"></div>

  <div class="card card-green">
    <h3>✅ What Worked Well</h3>
    <p id="fb-worked"></p>
  </div>
  <div class="card card-yellow">
    <h3>💡 Areas for Improvement</h3>
    <p id="fb-improve"></p>
  </div>
  <div class="card card-blue">
    <h3>✍️ Expert Rewrite</h3>
    <p id="fb-rewrite" style="white-space:pre-wrap;"></p>
  </div>
  <div class="card card-purple">
    <h3>📌 Core Lesson to Remember</h3>
    <p id="fb-lesson" style="font-weight:600;font-style:italic;"></p>
  </div>
  <div class="btn-row">
    <button class="btn btn-primary" onclick="showPage('tutor-setup')">📋 Try Another Scenario</button>
    <button class="btn btn-secondary" onclick="showPage('tutor-draft')">🔁 Rewrite Same Scenario</button>
    <button class="btn btn-secondary" onclick="showPage('quiz-setup')">📝 Go to Quiz</button>
  </div>
</div>

</div><!-- /main -->
</div><!-- /shell -->

<script>
// ── State ────────────────────────────────────────────────────────────────────
let questions = [];
let qIndex = 0;
let answers = [];
let currentScenario = null;

const SCENARIOS = [
  {title:"First-Time Donor Thank-You", description:"A first-time donor named Rachel Kim just made a $150 donation to your organization, 'Bright Futures Foundation', which provides after-school tutoring to low-income students. Write a thank-you email to Rachel that acknowledges her gift, explains the impact, informs her of any tax-deductibility, and makes her feel genuinely appreciated. Your organization's EIN is 82-3456789."},
  {title:"Year-End Matching Gift Appeal", description:"Your organization, 'Clean Water Now', is running a year-end campaign. A board member has pledged to match all gifts up to $20,000, but only until December 31. You have raised $12,000 so far and need $8,000 more. Write a fundraising appeal email to your donor list that creates urgency, explains the matching gift opportunity, and includes a clear call to action. The deadline is in 5 days."},
  {title:"Lapsed Donor Re-Engagement", description:"A donor named Thomas Webb gave $500 last year but has not donated this year. Your organization, 'Second Harvest Food Bank', wants to re-engage him. Write a re-engagement email that acknowledges his past support, shares a recent impact story, and invites him to renew his support — without sounding pushy or making him feel guilty."},
  {title:"Volunteer Appreciation & Recruitment", description:"Your organization, 'Literacy Bridge', is running low on tutoring volunteers. Write an email to your existing volunteer and donor list that: (1) thanks current volunteers, (2) shares a specific impact metric, and (3) makes a targeted ask for new volunteer sign-ups with clear commitment details — including hours per week and minimum time commitment."},
  {title:"Grant Reporting Reminder", description:"Your foundation just awarded a $30,000 grant to a partner organization. Write a formal email reminding the grantee of their reporting requirements, the reporting schedule, what happens if reports are late, and when the second installment of funds will be released."},
  {title:"Planned Giving Introduction", description:"A long-time major donor, Eleanor Davis (age 68), has expressed interest in leaving a legacy gift. Write a warm, respectful email from your organization 'Arts & Culture Alliance' introducing her to planned giving options (bequests, beneficiary designations, etc.), the benefits of joining your legacy society, and who she can contact. Do NOT use unexplained legal jargon."}
];

// ── Navigation ───────────────────────────────────────────────────────────────
function showPage(id){
  document.querySelectorAll('[id^="page-"]').forEach(el=>el.classList.add('hidden'));
  document.getElementById('page-'+id).classList.remove('hidden');
}

// ── Scenario Preview ─────────────────────────────────────────────────────────
function updateScenarioPreview(){
  const val = document.getElementById('scenario-select').value;
  const box = document.getElementById('scenario-preview');
  if(val==='random'){box.textContent='A random scenario will be chosen when you start.'; return;}
  const s = SCENARIOS[parseInt(val)];
  box.innerHTML='<strong>'+s.title+'</strong><br><br>'+s.description;
}

function startTutor(){
  const val = document.getElementById('scenario-select').value;
  if(val==='random') currentScenario = SCENARIOS[Math.floor(Math.random()*SCENARIOS.length)];
  else currentScenario = SCENARIOS[parseInt(val)];
  document.getElementById('tutor-scenario-display').innerHTML='<strong>'+currentScenario.title+'</strong><br><br>'+currentScenario.description;
  document.getElementById('tutor-draft').value='';
  showPage('tutor-draft');
}

// ── Quiz ─────────────────────────────────────────────────────────────────────
async function startQuiz(){
  const n = document.getElementById('num-q').value;
  document.getElementById('quiz-gen-spinner').classList.remove('hidden');
  document.getElementById('quiz-setup-error').classList.add('hidden');
  try{
    const res = await fetch('/api/generate_quiz',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({num_questions:parseInt(n)})});
    const data = await res.json();
    if(data.error){showError('quiz-setup-error',data.error);return;}
    questions = data.questions;
    qIndex = 0; answers = [];
    showQuestion();
    showPage('quiz-question');
  }catch(e){showError('quiz-setup-error','Failed to generate questions. Check your API key and try again.');}
  finally{document.getElementById('quiz-gen-spinner').classList.add('hidden');}
}

function showQuestion(){
  const q = questions[qIndex];
  const total = questions.length;
  document.getElementById('q-progress').style.width=((qIndex/total)*100)+'%';
  document.getElementById('q-counter').textContent='Q'+(qIndex+1)+' of '+total;
  document.getElementById('q-meta').textContent=q.topic+' · '+q.difficulty.toUpperCase();
  document.getElementById('q-text').textContent=q.question;
  document.getElementById('q-feedback').classList.add('hidden');
  document.getElementById('q-options').innerHTML='';
  document.getElementById('q-shortanswer').classList.add('hidden');
  document.getElementById('q-hint').classList.add('hidden');
  document.getElementById('q-hint').textContent=q.hint||'';
  document.getElementById('q-submit-btn').disabled=false;
  document.getElementById('q-spinner').classList.add('hidden');
  document.getElementById('q-next-btn').classList.remove('hidden');
  document.getElementById('q-finish-btn').classList.add('hidden');
  if(qIndex+1===total) {document.getElementById('q-next-btn').classList.add('hidden'); document.getElementById('q-finish-btn').classList.remove('hidden');}

  if(q.type==='mcq'||q.type==='true_false'){
    const opts = document.getElementById('q-options');
    Object.entries(q.options).forEach(([k,v])=>{
      opts.innerHTML+=`<label class="option-label" id="opt-${k}"><input type="radio" name="mcq" value="${k}"/> ${k}. ${v}</label>`;
    });
  } else {
    document.getElementById('q-shortanswer').classList.remove('hidden');
    document.getElementById('sa-input').value='';
  }
}

function toggleHint(){
  document.getElementById('q-hint').classList.toggle('hidden');
}

async function submitAnswer(){
  const q = questions[qIndex];
  let userAnswer='';
  if(q.type==='mcq'||q.type==='true_false'){
    const sel=document.querySelector('input[name="mcq"]:checked');
    if(!sel){alert('Please select an answer.');return;}
    userAnswer=sel.value;
  } else {
    userAnswer=document.getElementById('sa-input').value.trim();
    if(!userAnswer){alert('Please type your answer.');return;}
  }
  document.getElementById('q-spinner').classList.remove('hidden');
  document.getElementById('q-submit-btn').disabled=true;
  try{
    const res=await fetch('/api/evaluate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,user_answer:userAnswer})});
    const fb=await res.json();
    answers.push({question:q.question,topic:q.topic,difficulty:q.difficulty,is_correct:fb.is_correct,correct_answer:fb.correct_answer,explanation:fb.explanation});
    // Show feedback
    const fbox=document.getElementById('q-feedback-box');
    fbox.className='feedback-box '+(fb.is_correct?'feedback-correct':'feedback-wrong');
    fbox.innerHTML=fb.is_correct?'<strong>✅ Correct!</strong>':'<strong>❌ Incorrect</strong> — Correct answer: <strong>'+fb.correct_answer+'</strong>';
    document.getElementById('q-explanation').innerHTML='<h3>'+(fb.is_correct?'🌟 Tutor Feedback':'📚 Explanation')+'</h3><p>'+fb.explanation+'</p>';
    if(fb.source_subjects&&fb.source_subjects.length)
      document.getElementById('q-sources').textContent='📧 Sources: '+fb.source_subjects.slice(0,3).join(' · ');
    // Highlight options
    if(q.type==='mcq'||q.type==='true_false'){
      document.querySelectorAll('.option-label').forEach(el=>{el.style.cursor='default';});
      const correctEl=document.getElementById('opt-'+fb.correct_answer.charAt(0));
      if(correctEl) correctEl.classList.add('correct-opt');
      if(!fb.is_correct){
        const wrongEl=document.getElementById('opt-'+userAnswer);
        if(wrongEl) wrongEl.classList.add('wrong-opt');
      }
    }
    document.getElementById('q-feedback').classList.remove('hidden');
  }catch(e){alert('Evaluation failed. Please try again.');}
  finally{document.getElementById('q-spinner').classList.add('hidden');}
}

function nextQuestion(){
  qIndex++;
  if(qIndex<questions.length) showQuestion();
  else showResults();
}

function showResults(){
  const total=answers.length;
  const correct=answers.filter(a=>a.is_correct).length;
  const pct=Math.round(correct/total*100);
  document.getElementById('results-score').textContent=correct+' / '+total;
  const grade=document.getElementById('results-grade');
  if(pct>=80) grade.innerHTML='🏆 <strong>Excellent!</strong> Strong understanding of non-profit donor communication.';
  else if(pct>=60) grade.innerHTML='📚 <strong>Good effort!</strong> Review the explanations below to strengthen your knowledge.';
  else grade.innerHTML='💪 <strong>Keep practising!</strong> Read through the explanations below to improve.';
  const tbody=document.getElementById('results-table');
  tbody.innerHTML='';
  const weak=new Set();
  answers.forEach((a,i)=>{
    if(!a.is_correct) weak.add(a.topic);
    tbody.innerHTML+=`<tr><td>${i+1}</td><td style="max-width:300px">${a.question.substring(0,60)}...</td><td><span class="badge ${a.is_correct?'badge-green':'badge-red'}">${a.is_correct?'✅ Correct':'❌ Wrong'}</span></td><td>${a.topic}</td></tr>`;
  });
  const weakDiv=document.getElementById('results-weak');
  if(weak.size){
    weakDiv.innerHTML='<h3 style="margin-bottom:10px;">🎯 Topics to Review</h3>'+[...weak].map(t=>`<div class="info-strip" style="margin:5px 0;">📌 ${t}</div>`).join('');
  } else weakDiv.innerHTML='';
  showPage('quiz-results');
}

// ── Tutor Draft ──────────────────────────────────────────────────────────────
async function submitDraft(){
  const draft=document.getElementById('tutor-draft').value.trim();
  if(draft.length<30){showError('tutor-draft-error','Please write a longer draft (at least a few sentences).');return;}
  document.getElementById('tutor-spinner').classList.remove('hidden');
  document.getElementById('tutor-draft-error').classList.add('hidden');
  try{
    const res=await fetch('/api/evaluate_draft',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scenario:currentScenario,draft})});
    const data=await res.json();
    if(data.error){showError('tutor-draft-error',data.error);return;}
    const score=data.score_out_of_10||0;
    const scoreBox=document.getElementById('tutor-score-box');
    const color=score>=8?'#10b981':score>=6?'#f59e0b':'#ef4444';
    scoreBox.innerHTML=`<span style="color:${color};font-size:36px;">${score}/10</span><br/><span style="font-size:14px;color:#6b7280;">${score>=8?'Excellent! 🏆':score>=6?'Good Effort! 📚':'Needs Improvement 💪'}</span>`;
    document.getElementById('fb-worked').textContent=data.what_worked_well||'—';
    document.getElementById('fb-improve').textContent=data.areas_for_improvement||'—';
    document.getElementById('fb-rewrite').textContent=data.expert_rewrite||'—';
    document.getElementById('fb-lesson').textContent=data.core_lesson||'—';
    showPage('tutor-feedback');
  }catch(e){showError('tutor-draft-error','Evaluation failed. Check your API key and try again.');}
  finally{document.getElementById('tutor-spinner').classList.add('hidden');}
}

function showError(id,msg){
  const el=document.getElementById(id);
  el.textContent=msg;
  el.classList.remove('hidden');
}
</script>
</body>
</html>"""

# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/generate_quiz", methods=["POST"])
def api_generate_quiz():
    try:
        data = request.get_json()
        num_q = int(data.get("num_questions", 5))
        from question_generator import generate_quiz
        questions = generate_quiz(num_questions=num_q)
        return jsonify({"questions": questions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/evaluate", methods=["POST"])
def api_evaluate():
    try:
        data = request.get_json()
        question = data["question"]
        user_answer = data["user_answer"]
        from evaluator import evaluate_answer
        result = evaluate_answer(question, user_answer)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/evaluate_draft", methods=["POST"])
def api_evaluate_draft():
    try:
        data = request.get_json()
        scenario = data["scenario"]
        draft = data["draft"]
        from writing_tutor import _evaluate_draft
        result = _evaluate_draft(scenario, draft)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    # Auto-ingest if DB missing
    if not os.path.exists(config.CHROMA_DB_PATH):
        print("Vector DB not found — running ingestion first...")
        from ingest import run_ingestion
        run_ingestion()
    print("\n🎓 Non-Profit Quiz/Tutor Bot is running!")
    print("   Open your browser at: http://localhost:5000\n")
    app.run(debug=False, port=5000, host="0.0.0.0")
