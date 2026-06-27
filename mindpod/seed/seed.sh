#!/usr/bin/env bash
set -euo pipefail

echo "🌱 Seeding MindPod with demo data..."

POD="mindpod"

# ── Insert demo sessions ──
echo "  → Creating demo sessions..."

lemma tables insert "$POD" sessions \
  --data '{"goal":"Help me study the basics of machine learning — I have an exam next week","mode":"learn","status":"done","agent_mode":"learn","summary":"Created 12 flashcards and 5 quiz questions covering supervised vs unsupervised learning, gradient descent, and overfitting.","sources_used":"[\"/knowledge/ml-notes.pdf\"]"}'

lemma tables insert "$POD" sessions \
  --data '{"goal":"Analyze our Q3 revenue data and find growth opportunities","mode":"analyze","status":"done","agent_mode":"analyze","summary":"EDA complete. Enterprise tier drives 61% of ARR. Churn strongly anti-correlated with onboarding completion. 3 anomalies flagged.","sources_used":"[\"/data/revenue.csv\",\"/data/churn.csv\"]"}'

# ── Insert demo insights ──
echo "  → Creating demo insights..."

S1=$(lemma tables query "$POD" sessions --filter 'mode=learn' --limit 1 --field id)
S2=$(lemma tables query "$POD" sessions --filter 'mode=analyze' --limit 1 --field id)

lemma tables insert "$POD" insights \
  --data "{\"session_id\":\"$S2\",\"insight_type\":\"finding\",\"content\":\"Q3 revenue grew 23% YoY, driven primarily by the Enterprise tier which now represents 61% of ARR.\",\"source\":\"/data/revenue.csv\",\"confidence\":\"high\",\"agent\":\"data-agent\"}"

lemma tables insert "$POD" insights \
  --data "{\"session_id\":\"$S2\",\"insight_type\":\"pattern\",\"content\":\"Churn rate is inversely correlated with onboarding completion (r = -0.72). Users completing all 5 onboarding steps churn at 2.1% vs 14.3% for those who skip.\",\"source\":\"/data/churn.csv\",\"confidence\":\"high\",\"agent\":\"data-agent\"}"

lemma tables insert "$POD" insights \
  --data "{\"session_id\":\"$S2\",\"insight_type\":\"anomaly\",\"content\":\"September shows an unusual 40% spike in support tickets despite no product release in that period. Possible external cause warrants investigation.\",\"source\":\"/data/support.csv\",\"confidence\":\"medium\",\"agent\":\"data-agent\"}"

lemma tables insert "$POD" insights \
  --data "{\"session_id\":\"$S2\",\"insight_type\":\"action\",\"content\":\"Prioritize onboarding completion for new users — closing the completion gap to 100% could reduce churn by ~8.5pp based on current regression.\",\"source\":\"/data/churn.csv\",\"confidence\":\"high\",\"agent\":\"data-agent\"}"

# ── Insert demo study items ──
echo "  → Creating demo study items..."

lemma tables insert "$POD" study_items \
  --data "{\"session_id\":\"$S1\",\"item_type\":\"flashcard\",\"topic\":\"Supervised vs Unsupervised Learning\",\"question\":\"What is the key difference between supervised and unsupervised learning?\",\"answer\":\"Supervised: trained on labeled data (input→output pairs). Unsupervised: finds patterns in unlabeled data. Classification is supervised; clustering is unsupervised.\",\"difficulty\":\"easy\",\"source_page\":\"ml-notes.pdf p.3\"}"

lemma tables insert "$POD" study_items \
  --data "{\"session_id\":\"$S1\",\"item_type\":\"quiz_question\",\"topic\":\"Gradient Descent\",\"question\":\"What does learning rate control in gradient descent, and what happens if it's too high?\",\"answer\":\"Learning rate controls the step size when updating weights. Too high: overshoots the minimum and training diverges. Too low: very slow convergence.\",\"difficulty\":\"medium\",\"source_page\":\"ml-notes.pdf p.11\"}"

lemma tables insert "$POD" study_items \
  --data "{\"session_id\":\"$S1\",\"item_type\":\"weak_area\",\"topic\":\"Backpropagation\",\"question\":\"Chain rule derivation for deep networks — this section is underexplained in the notes.\",\"answer\":\"Review 3Blue1Brown 'Backpropagation calculus' video and Chapter 6 of Nielsen's Neural Networks and Deep Learning.\",\"difficulty\":\"hard\",\"source_page\":\"ml-notes.pdf p.18\"}"

echo ""
echo "✅ Seed data loaded!"
echo "   Open the app and check the Insights + Study tabs."
