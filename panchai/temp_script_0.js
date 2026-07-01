
    // Injected or fallback configuration
    const lemmaConfig = window.__LEMMA_CONFIG__ || {};
    const client = window.LemmaClient?.LemmaClient
      ? new window.LemmaClient.LemmaClient({
          apiUrl: lemmaConfig.apiUrl || window.__LEMMA_BASE_URL__ || 'https://api.lemma.work',
          timeoutMs: 120000
        })
      : null;
    if (client && !client.podId) {
      const podId = lemmaConfig.podId || window.__LEMMA_POD_ID__;
      if (podId) client.setPodId(podId);
    }

    // State Variables
    let lemmaConnected = false;
    let activeSessionId = null;
    let feedSubscription = null;
    let sessionSubscription = null;
    let currentWorkflowRunId = null;
    let formNodeId = null;
    let isSimulationActive = false;
    let simulationTimeoutIds = [];
    
    // In-memory Database for Simulation Mode
    let simSessions = [
      {
        id: "sim-yesmadam-1",
        client_id: "yesmadam",
        task_input: "Should we approve this refund for Customer #4821? Customer tier Gold, purchase 47 days ago, policy = 30-day returns, claim = product defect, 2 prior refunds in 6 months.",
        user_goal: "Approve the refund",
        stripped_task: "Refund request evaluation: Customer Gold tier, purchase 47 days ago, refund window 30 days, claim is product defect, 2 prior refunds in 6 months.",
        stakes_level: "HIGH",
        status: "done"
      },
      {
        id: "sim-binocs-1",
        client_id: "binocs",
        task_input: "Should we pause this vendor order? Inventory 340 units, demand forecast 280 units, vendor reliability 62%, lead time 45 days, cash position tight.",
        user_goal: "Pause the vendor order",
        stripped_task: "Vendor order evaluation: Inventory 340 units, demand forecast 280 units, reliability 62%, lead time 45 days, cash status tight.",
        stakes_level: "STANDARD",
        status: "done"
      }
    ];

    let simVerdicts = {
      "sim-yesmadam-1": {
        session_id: "sim-yesmadam-1",
        verdict: "ESCALATED",
        confidence_score: 0.58,
        council_vote_for: ["customer-advocate"],
        council_vote_against: ["policy-analyst", "fraud-risk-assessor"],
        council_vote_abstain: [],
        council_vote_reframe: [],
        conflict_report: {
          user_goal: "Approve the refund",
          council_finding: "Reject or escalate pending defect verification because the request is outside the 30-day return window and has repeating refund flags.",
          divergence_severity: "HIGH"
        },
        recommended_action: "Escalate to a human approver with defect evidence and refund-history context.",
        hitl_required: true,
        hitl_reason: "High divergence from user goal and low confidence require human review."
      },
      "sim-binocs-1": {
        session_id: "sim-binocs-1",
        verdict: "REFRAMED",
        confidence_score: 0.72,
        council_vote_for: [],
        council_vote_against: [],
        council_vote_abstain: [],
        council_vote_reframe: ["supply-chain-analyst", "financial-risk", "procurement-specialist"],
        conflict_report: {
          user_goal: "Pause the vendor order",
          council_finding: "Reframe to a partial staggered order with payment renegotiation, preserving supply coverage while easing cash pressure.",
          divergence_severity: "MEDIUM"
        },
        recommended_action: "Proceed with a partial order (150 units) and renegotiated payment terms.",
        hitl_required: false,
        hitl_reason: "Consensus reframe with adequate confidence."
      }
    };

    let simMessages = {
      "sim-yesmadam-1": [
        { round_number: 0, agent_name: "policy-analyst", reasoning_bias: "rule-following", position: "PREMORTEM", argument: "Pre-Mortem: If this refund fails, it will be because we created a policy exception without verifying the product defect, leading to policy erosion. The assumption most likely to be wrong is that the customer's defect claim is legitimate without verification. Harmed: YesMadam finance team." },
        { round_number: 0, agent_name: "customer-advocate", reasoning_bias: "empathetic", position: "PREMORTEM", argument: "Pre-Mortem: If this refund fails, it will be because we denied a Gold member, causing them to leave and post a negative review. The assumption most likely to be wrong is that a refund exception creates fraud risk rather than long-term customer value. Harmed: Brand reputation." },
        { round_number: 0, agent_name: "fraud-risk-assessor", reasoning_bias: "conservative", position: "PREMORTEM", argument: "Pre-Mortem: If this refund fails, it will be because we ignored the pattern of 2 prior refunds in 6 months, enabling a refund-abuse vector. The assumption most likely to be wrong is that Gold status excludes malicious exploitation. Harmed: Bottom-line profitability." },
        { round_number: 1, agent_name: "customer-advocate", reasoning_bias: "empathetic", position: "FOR", argument: "I vote FOR approving the refund. This is a Gold-tier customer with 2 years of tenure. A product defect claim is legally distinct and falls under consumer rights, which override standard 30-day limits. Let's prioritize customer retention." },
        { round_number: 1, agent_name: "policy-analyst", reasoning_bias: "rule-following", position: "REFRAME", argument: "I propose REFRAME. We lack specific evidence of the defect. We should verify the defect first, and if valid, apply a structured tier-based exception. We shouldn't make a binary decision without checking the facts." },
        { round_number: 1, agent_name: "fraud-risk-assessor", reasoning_bias: "conservative", position: "AGAINST", argument: "I vote AGAINST. The customer has already had 2 refunds in the last 6 months. This is a clear abuse pattern. Gold status shouldn't override audit flags." },
        { round_number: 1, agent_name: "panchai-brain", reasoning_bias: "Moderator", position: "MODERATOR", argument: "Moderator Challenge: Fraud Risk Assessor cites a clear refund abuse pattern, while Customer Advocate argues Gold tier tenure earns a presumption of good faith. Policy Analyst proposes a verification check. Customer Advocate, how do you justify overriding the fraud flag? Fraud Risk, is there a threshold of tenure where exception review is warranted?" },
        { round_number: 2, agent_name: "customer-advocate", reasoning_bias: "empathetic", position: "FOR", argument: "In response to Fraud Risk: Yes, 2 refunds is a signal, but for a Gold customer over 2 years, the total transaction volume is high. We should apply standard identity check, and if passed, approve it. Denying them over a defect claim is a higher brand risk." },
        { round_number: 2, agent_name: "policy-analyst", reasoning_bias: "rule-following", position: "REFRAME", argument: "Building on both responses: The customer advocate operates from principle (loyalty deserves protection) and the fraud assessor from principle (risk must be verified independently). Both are valid. I propose a middle path: a tiered evaluation framework where Gold 2-year members receive an enhanced review protocol that includes (1) identity confirmation, (2) transaction pattern check, and (3) escalated approval if anomalous. This reframes the debate." },
        { round_number: 2, agent_name: "fraud-risk-assessor", reasoning_bias: "conservative", position: "AGAINST", argument: "In response to Customer Advocate: Loyalty is not a shield against abuse. Standard verification is not enough. I shift to a conditional position: I am AGAINST approval unless senior operations manually inspect the defect history." },
        { round_number: 2, agent_name: "panchai-brain", reasoning_bias: "Moderator", position: "MODERATOR", argument: "Moderator Challenge: Round 2 has produced progress. Policy Analyst proposes a structured verification framework, while Fraud Risk has shifted to conditional opposition. Let's lock in final positions on this structured protocol. Do we accept the Policy Analyst's 3-step verification system?" },
        { round_number: 3, agent_name: "policy-analyst", reasoning_bias: "rule-following", position: "REFRAME", argument: "FINAL POSITION: Formal proposal for Gold-tier members ΓÇö adopt verification protocol: (1) Identity confirmation, (2) Transaction pattern consistency, (3) If either flags, escalate to senior review. This converts the philosophical divide into operational guidance." },
        { round_number: 3, agent_name: "customer-advocate", reasoning_bias: "empathetic", position: "FOR", argument: "FINAL POSITION: After considering the fraud risk assessor's concerns about exploitation and the policy analyst's call for structured evaluation, I maintain my FOR position but with nuance. I accept that blind trust is not appropriate. Let's presume good faith but apply basic checks." },
        { round_number: 3, agent_name: "fraud-risk-assessor", reasoning_bias: "conservative", position: "AGAINST", argument: "FINAL POSITION: Still AGAINST blanket approval. Loyalty is not a shield against abuse. Gold tenure should earn a thorough review, not a shortcut." }
      ],
      "sim-binocs-1": [
        { round_number: 0, agent_name: "supply-chain-analyst", reasoning_bias: "operational-continuity", position: "PREMORTEM", argument: "Pre-Mortem: If we pause the order, we will run out of inventory in 45 days due to lead times, breaking supply continuity. Wrong assumption: Demand will stay low or lead times don't matter. Harmed: Delivery speed & client satisfaction." },
        { round_number: 0, agent_name: "financial-risk", reasoning_bias: "cash-preservation", position: "PREMORTEM", argument: "Pre-Mortem: If we don't pause the order, we will experience a cash flow crisis, unable to pay other vendors. Wrong assumption: Cash buffer is sufficient. Harmed: Company liquidity." },
        { round_number: 0, agent_name: "procurement-specialist", reasoning_bias: "vendor-relationship", position: "PREMORTEM", argument: "Pre-Mortem: If we pause the order, we will damage our relationship with this key vendor, who has a 62% reliability score already. Wrong assumption: Vendor will easily resume shipping later. Harmed: Sourcing network." },
        { round_number: 1, agent_name: "supply-chain-analyst", reasoning_bias: "operational-continuity", position: "REFRAME", argument: "Pausing is too binary. 45-day lead time is too long. I propose a partial, staggered order." },
        { round_number: 1, agent_name: "financial-risk", reasoning_bias: "cash-preservation", position: "REFRAME", argument: "I support a reframe. We must preserve cash, but a complete pause breaks supply. Let's renegotiate payment terms to split the bill." },
        { round_number: 1, agent_name: "procurement-specialist", reasoning_bias: "vendor-relationship", position: "REFRAME", argument: "I agree with a reframe. Stagger the order and offer vendor 50% upfront, 50% net-60 to preserve the relationship." },
        { round_number: 1, agent_name: "panchai-brain", reasoning_bias: "Moderator", position: "MODERATOR", argument: "Moderator Challenge: The council is in consensus to REFRAME. All members agree a binary pause is dangerous. Supply Chain proposes staggered order, Finance proposes split billing, Procurement proposes net-60. Let's align on a unified proposal." },
        { round_number: 2, agent_name: "supply-chain-analyst", reasoning_bias: "operational-continuity", position: "REFRAME", argument: "We should order 150 units now (covering demand next 25 days) instead of 300, and place the rest next month." },
        { round_number: 2, agent_name: "financial-risk", reasoning_bias: "cash-preservation", position: "REFRAME", argument: "Staggering order to 150 units cuts immediate cost by 50%. This keeps cash within safety margins." },
        { round_number: 2, agent_name: "procurement-specialist", reasoning_bias: "vendor-relationship", position: "REFRAME", argument: "I will draft the staggered order terms with split Net-45 payments. Vendor will accept this because it maintains order continuity." }
      ]
    };

    // UI Elements
    const sessionSelect = document.getElementById('session-select');
    const tabs = document.querySelectorAll('.tab');
    const views = document.querySelectorAll('.view');
    const feedContainer = document.getElementById('feed-container');
    const hitlSubmitBtn = document.getElementById('hitl-submit-btn');

    // Tab Switching
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.target).classList.add('active');
      });
    });

    // Architecture Stepper & Tour Syncer
    function showTourStep(phaseIndex) {
      // Switch to Tour tab
      tabs[0].click();
      
      // Remove highlighting
      for (let i = 0; i <= 5; i++) {
        const card = document.getElementById(`tour-card-${i}`);
        if (card) card.classList.remove('active-tour');
      }
      
      // Highlight the targeted card
      const targetCard = document.getElementById(`tour-card-${phaseIndex}`);
      if (targetCard) {
        targetCard.classList.add('active-tour');
        targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Add a temporary glow effect
        targetCard.style.boxShadow = "0 0 30px rgba(99, 102, 241, 0.4)";
        setTimeout(() => {
          targetCard.style.boxShadow = "";
        }, 1500);
      }
    }

    // Connection setup
    function setConnectionStatus(ok, text) {
      const dot = document.getElementById('conn-dot');
      const label = document.getElementById('conn-text');
      if (ok) {
        dot.className = 'status-badge-dot connected';
        label.textContent = text;
      } else {
        dot.className = 'status-badge-dot';
        label.textContent = text;
      }
    }

    // Initialize App
    async function initApp() {
      lucide.createIcons();
      
      if (!client) {
        setConnectionStatus(false, 'Simulation Mode');
        lemmaConnected = false;
        loadSessions();
      } else {
        try {
          await client.initialize();
          if (client.podId) {
            lemmaConnected = true;
            setConnectionStatus(true, 'Live Pod Mode');
            loadSessions();
          } else {
            lemmaConnected = false;
            setConnectionStatus(false, 'Simulation Mode');
            loadSessions();
          }
        } catch (err) {
          console.warn('Lemma SDK initialization failed, entering simulation mode.', err);
          lemmaConnected = false;
          setConnectionStatus(false, 'Simulation Mode');
          loadSessions();
        }
      }

      sessionSelect.addEventListener('change', (e) => {
        if (e.target.value) {
          setActiveSession(e.target.value);
        } else {
          showHero();
        }
      });

      document.getElementById('new-session-btn').addEventListener('click', showIntakeModal);
      
      // HITL Form states
      const radios = document.querySelectorAll('input[name="hitl_decision"]');
      const reasonInput = document.getElementById('hitl-reason-input');
      
      const checkFormState = () => {
        const decision = document.querySelector('input[name="hitl_decision"]:checked')?.value;
        const reason = reasonInput.value.trim();
        if (decision === 'approve') {
          hitlSubmitBtn.disabled = false;
        } else if ((decision === 'reject' || decision === 'send_back') && reason.length > 5) {
          hitlSubmitBtn.disabled = false;
        } else {
          hitlSubmitBtn.disabled = true;
        }
      };

      radios.forEach(r => r.addEventListener('change', checkFormState));
      reasonInput.addEventListener('input', checkFormState);
      
      hitlSubmitBtn.addEventListener('click', submitHitlDecision);
    }

    function showHero() {
      activeSessionId = null;
      clearSimulation();
      
      // Reset feed
      feedContainer.innerHTML = '';
      const hero = document.getElementById('hero-section');
      if (hero) {
        feedContainer.appendChild(hero);
        hero.style.display = 'flex';
      }
      
      document.getElementById('verdict-container').style.display = 'none';
      document.getElementById('verdict-empty').style.display = 'flex';
      
      // Reset sidebar values
      document.getElementById('meta-client').textContent = '—';
      document.getElementById('meta-goal').textContent = '—';
      document.getElementById('meta-stripped').textContent = '—';
      document.getElementById('meta-status-text').textContent = 'Waiting for session...';
      document.getElementById('meta-status-dot').className = 'status-dot';
      
      // Reset stepper
      for (let i = 0; i <= 5; i++) {
        const el = document.getElementById(`arch-step-${i}`);
        if (el) el.classList.remove('active', 'completed');
      }
      
      lucide.createIcons();
    }

    async function loadSessions() {
      if (lemmaConnected) {
        try {
          const response = await client.records.list("debate_sessions", { 
            sort: [{ field: "created_at", direction: "desc" }] 
          });
          
          sessionSelect.innerHTML = '<option value="">-- Select a Session --</option>';
          if (response.items && response.items.length > 0) {
            response.items.forEach(session => {
              const opt = document.createElement('option');
              opt.value = session.id;
              const shortGoal = session.task_input ? session.task_input.substring(0, 45) + '...' : 'Unknown Task';
              opt.textContent = `${session.client_id.toUpperCase()} - ${shortGoal}`;
              sessionSelect.appendChild(opt);
            });
          }
        } catch (err) {
          console.error("Error loading sessions from SDK:", err);
          loadSimSessionsDropdown();
        }
      } else {
        loadSimSessionsDropdown();
      }
    }

    function loadSimSessionsDropdown() {
      sessionSelect.innerHTML = '<option value="">-- Select a Session --</option>';
      simSessions.forEach(session => {
        const opt = document.createElement('option');
        opt.value = session.id;
        const shortGoal = session.task_input ? session.task_input.substring(0, 45) + '...' : 'Unknown Task';
        opt.textContent = `[SIM] ${session.client_id.toUpperCase()} - ${shortGoal}`;
        sessionSelect.appendChild(opt);
      });
    }

    function updateStatusIndicator(status) {
      const dot = document.getElementById('meta-status-dot');
      const text = document.getElementById('meta-status-text');
      
      dot.className = 'status-dot';
      
      const statusMap = {
        'pending': { label: 'Pending', active: true },
        'stripping': { label: 'Stripping Goal', active: true },
        'pre_mortem': { label: 'Pre-Mortem Phase', active: true },
        'debating': { label: 'Active Debate', active: true },
        'voting': { label: 'Synthesizing Verdict', active: true },
        'verdict': { label: 'Verdict Reached', active: false, done: true },
        'hitl': { label: 'Awaiting Human Approval', active: false, hitl: true },
        'done': { label: 'Completed', active: false, done: true }
      };
      
      const info = statusMap[status] || { label: status, active: false };
      text.textContent = info.label;
      if (info.active) dot.classList.add('active');
      if (info.done) dot.classList.add('done');
      if (info.hitl) dot.classList.add('hitl');
      
      updateArchitectureStep(status);
    }

    function updateArchitectureStep(status) {
      for (let i = 0; i <= 5; i++) {
        const el = document.getElementById(`arch-step-${i}`);
        if (el) el.classList.remove('active', 'completed');
      }

      const stepStates = {
        'pending':     { active: [0], completed: [] },
        'stripping':   { active: [0], completed: [] },
        'pre_mortem':  { active: [1, 2], completed: [0] },
        'debating':    { active: [3], completed: [0, 1, 2] },
        'voting':      { active: [4], completed: [0, 1, 2, 3] },
        'verdict':     { active: [], completed: [0, 1, 2, 3, 4, 5] },
        'hitl':        { active: [5], completed: [0, 1, 2, 3, 4] },
        'done':        { active: [], completed: [0, 1, 2, 3, 4, 5] }
      };

      const state = stepStates[status] || { active: [], completed: [] };

      state.completed.forEach(idx => {
        const el = document.getElementById(`arch-step-${idx}`);
        if (el) el.classList.add('completed');
      });

      state.active.forEach(idx => {
        const el = document.getElementById(`arch-step-${idx}`);
        if (el) el.classList.add('active');
      });
    }

    async function setActiveSession(sessionId) {
      activeSessionId = sessionId;
      clearSimulation();
      
      // Hide hero
      const hero = document.getElementById('hero-section');
      if (hero) hero.style.display = 'none';
      
      // Setup feed skeleton
      feedContainer.innerHTML = '<div id="feed-empty" class="empty-state"><i data-lucide="message-square" class="icon-xl" style="width:48px;height:48px;"></i><h3>Starting Deliberation...</h3><p>The council is assembling to review this task.</p></div>';
      lucide.createIcons();

      // Reset Verdict dashboard
      document.getElementById('verdict-container').style.display = 'none';
      document.getElementById('verdict-empty').style.display = 'flex';
      document.getElementById('hitl-form-container').style.display = 'none';
      
      // Check if simulation session
      if (sessionId.startsWith('sim-')) {
        const session = simSessions.find(s => s.id === sessionId);
        if (session) {
          updateSidebarSim(session);
          
          if (session.status === 'done' || session.status === 'hitl' || session.status === 'verdict') {
            loadVerdictSim(sessionId);
            loadMessagesSim(sessionId);
          } else {
            // Trigger simulated run
            runSimulation(session);
          }
        }
      } else {
        // SDK Mode
        try {
          const session = await client.records.get("debate_sessions", sessionId);
          updateSidebarSim(session);
          
          if (session.status === 'verdict' || session.status === 'done' || session.status === 'hitl') {
            await loadVerdict(sessionId);
            if (session.status === 'hitl') {
              document.getElementById('hitl-form-container').style.display = 'block';
              findWorkflowRun(sessionId);
            }
          }
          
          setupFeedSubscription(sessionId);
          setupSessionPolling(sessionId);
        } catch (err) {
          console.error("Error setting active session:", err);
        }
      }
    }

    function updateSidebarSim(session) {
      document.getElementById('meta-client').textContent = session.client_id.toUpperCase();
      document.getElementById('meta-goal').textContent = session.user_goal || session.task_input;
      document.getElementById('meta-stripped').textContent = session.stripped_task || "Pending goal stripping...";
      
      const stakesBadge = document.getElementById('meta-stakes');
      if (session.stakes_level === 'HIGH') {
        stakesBadge.className = 'badge high-stakes';
        stakesBadge.textContent = 'High Stakes';
      } else {
        stakesBadge.className = 'badge standard-stakes';
        stakesBadge.textContent = 'Standard Stakes';
      }
      
      updateStatusIndicator(session.status);
    }

    // ─── Simulation Engine for Hackathon Demo Videos ───
    function clearSimulation() {
      isSimulationActive = false;
      simulationTimeoutIds.forEach(id => clearTimeout(id));
      simulationTimeoutIds = [];
    }

    function runSimulation(session) {
      clearSimulation();
      isSimulationActive = true;
      
      // Reset local simulation arrays
      const sessionId = session.id;
      const client_id = session.client_id;
      
      // Step-by-step pipeline execution
      const queue = [];
      
      // Phase 0: Stripping
      queue.push({
        delay: 500,
        fn: () => {
          session.status = 'stripping';
          updateSidebarSim(session);
        }
      });
      
      // Phase 1: Pre-Mortem Forcing
      queue.push({
        delay: 2000,
        fn: () => {
          session.status = 'pre_mortem';
          updateSidebarSim(session);
          feedContainer.innerHTML = ''; // Clear skeleton
        }
      });
      
      // Load pre-mortems (Phase 0/1 round)
      const feedMsgs = simMessages[sessionId] || [];
      const preMortems = feedMsgs.filter(m => m.round_number === 0);
      
      preMortems.forEach((pm, index) => {
        queue.push({
          delay: 3500 + (index * 1500),
          fn: () => {
            if (!isSimulationActive) return;
            renderMessageCardSim(pm, -1);
            // Scroll to bottom
            const feedView = document.getElementById('view-feed');
            feedView.scrollTop = feedView.scrollHeight;
          }
        });
      });

      // Phase 3: Active Debate (Round 1)
      queue.push({
        delay: 8500,
        fn: () => {
          session.status = 'debating';
          updateSidebarSim(session);
        }
      });

      const round1 = feedMsgs.filter(m => m.round_number === 1);
      round1.forEach((msg, index) => {
        queue.push({
          delay: 10000 + (index * 1500),
          fn: () => {
            if (!isSimulationActive) return;
            renderMessageCardSim(msg, 0);
            const feedView = document.getElementById('view-feed');
            feedView.scrollTop = feedView.scrollHeight;
          }
        });
      });

      // Phase 3: Debate (Round 2)
      const round2 = feedMsgs.filter(m => m.round_number === 2);
      if (round2.length > 0) {
        round2.forEach((msg, index) => {
          queue.push({
            delay: 17000 + (index * 1500),
            fn: () => {
              if (!isSimulationActive) return;
              renderMessageCardSim(msg, 1);
              const feedView = document.getElementById('view-feed');
              feedView.scrollTop = feedView.scrollHeight;
            }
          });
        });
      }

      // Phase 3: Debate (Round 3)
      const round3 = feedMsgs.filter(m => m.round_number === 3);
      if (round3.length > 0) {
        round3.forEach((msg, index) => {
          queue.push({
            delay: 24000 + (index * 1500),
            fn: () => {
              if (!isSimulationActive) return;
              renderMessageCardSim(msg, 2);
              const feedView = document.getElementById('view-feed');
              feedView.scrollTop = feedView.scrollHeight;
            }
          });
        });
      }

      // Phase 4: Voting
      const finalDelay = round3.length > 0 ? 30000 : 17000;
      queue.push({
        delay: finalDelay,
        fn: () => {
          session.status = 'voting';
          updateSidebarSim(session);
        }
      });

      // Phase 5: Verdict Synthesis / HITL
      queue.push({
        delay: finalDelay + 1500,
        fn: () => {
          const finalStatus = simVerdicts[sessionId].hitl_required ? 'hitl' : 'done';
          session.status = finalStatus;
          updateSidebarSim(session);
          
          // Switch to Verdict Tab
          document.getElementById('tab-verdict').click();
          loadVerdictSim(sessionId);
          
          if (finalStatus === 'hitl') {
            document.getElementById('hitl-form-container').style.display = 'block';
          }
          
          // Update global counts
          incrementImpactMetrics();
        }
      });

      // Schedule timeouts
      queue.forEach(item => {
        const id = setTimeout(item.fn, item.delay);
        simulationTimeoutIds.push(id);
      });
    }

    function renderMessageCardSim(msg, currentRound) {
      const emptyState = document.getElementById('feed-empty');
      if (emptyState) emptyState.remove();
      
      const msgRound = msg.round_number;
      if (currentRound !== msgRound) {
        const div = document.createElement('div');
        div.className = 'round-divider';
        div.textContent = msgRound === 0 ? 'Phase: Pre-Mortem' : (msg.position === 'MODERATOR' ? 'Active Moderator' : `Debate Round ${msgRound}`);
        feedContainer.appendChild(div);
      }
      
      const isMod = msg.position === 'MODERATOR';
      const posClass = msgRound === 0 ? 'pos-PREMORTEM' : (isMod ? 'pos-MODERATOR' : `pos-${msg.position || 'ABSTAIN'}`);
      const posLabel = msgRound === 0 ? 'PRE-MORTEM' : (isMod ? 'MODERATOR CHALLENGE' : (msg.position || 'ABSTAIN'));
      
      const card = document.createElement('div');
      card.className = `message-card ${posClass}`;
      card.innerHTML = `
        <div class="message-header">
          <div class="agent-info">
            <div class="agent-avatar"><i data-lucide="${isMod ? 'scale' : 'bot'}" class="icon"></i></div>
            <div class="agent-details">
              <span class="agent-name">${isMod ? 'PANCHAI Moderator' : formatAgentName(msg.agent_name)}</span>
              <span class="agent-bias">${msg.reasoning_bias || 'Analyst'}</span>
            </div>
          </div>
          <div class="position-badge">${posLabel}</div>
        </div>
        <div class="message-body">${escapeHtml(msg.argument)}</div>
      `;
      
      feedContainer.appendChild(card);
      lucide.createIcons({ root: card });
    }

    function loadMessagesSim(sessionId) {
      feedContainer.innerHTML = '';
      const msgs = simMessages[sessionId] || [];
      let currentRound = -1;
      
      msgs.forEach(msg => {
        renderMessageCardSim(msg, currentRound);
        currentRound = msg.round_number;
      });
      
      const feedView = document.getElementById('view-feed');
      feedView.scrollTop = feedView.scrollHeight;
    }

    function loadVerdictSim(sessionId) {
      const v = simVerdicts[sessionId];
      if (!v) {
        document.getElementById('verdict-empty').style.display = 'flex';
        document.getElementById('verdict-container').style.display = 'none';
        return;
      }
      
      document.getElementById('verdict-empty').style.display = 'none';
      document.getElementById('verdict-container').style.display = 'grid';
      
      const vText = document.getElementById('vd-verdict-text');
      vText.textContent = v.verdict;
      vText.className = `verdict-large v-${v.verdict}`;
      document.getElementById('vd-reason').textContent = v.recommended_action || "Verdict compiled from multi-agent council.";
      
      // Confidence score
      const score = v.confidence_score || 0;
      const pct = Math.round(score * 100);
      document.getElementById('vd-confidence-text').textContent = `${pct}%`;
      
      const gaugeFill = document.getElementById('vd-gauge-fill');
      const dashOffset = 408 - (408 * score);
      gaugeFill.style.strokeDasharray = `${408 - dashOffset} 408`;
      
      let cColor = '#f43f5e'; // risk
      let cLabel = 'Low Consensus Confidence';
      if (score >= 0.75) { cColor = '#10b981'; cLabel = 'High Consensus Confidence'; }
      else if (score >= 0.6) { cColor = '#f59e0b'; cLabel = 'Moderate Consensus Confidence'; }
      
      gaugeFill.style.stroke = cColor;
      document.getElementById('vd-confidence-label').textContent = cLabel;
      
      // Vote segment lengths
      const forVotes = v.council_vote_for.length;
      const againstVotes = v.council_vote_against.length;
      const reframeVotes = v.council_vote_reframe.length;
      const total = forVotes + againstVotes + reframeVotes;
      
      const bar = document.getElementById('vd-vote-bar');
      bar.innerHTML = ''; // Clear prior segments
      
      if (total > 0) {
        if (forVotes > 0) {
          bar.innerHTML += `<div class="vote-segment seg-for" style="width: ${(forVotes/total)*100}%; background: var(--consensus);">${forVotes} FOR</div>`;
        }
        if (againstVotes > 0) {
          bar.innerHTML += `<div class="vote-segment seg-against" style="width: ${(againstVotes/total)*100}%; background: var(--risk);">${againstVotes} AGAINST</div>`;
        }
        if (reframeVotes > 0) {
          bar.innerHTML += `<div class="vote-segment" style="width: ${(reframeVotes/total)*100}%; background: var(--reframe);">${reframeVotes} REFRAME</div>`;
        }
      } else {
        bar.innerHTML = '<div class="vote-segment" style="width: 100%; background: var(--text-muted);">0 VOTES</div>';
      }

      // Votes list
      const votesContainer = document.getElementById('vd-agent-votes');
      votesContainer.innerHTML = '';
      const renderVote = (name, position) => {
        let posColor = 'var(--text-muted)';
        let iconName = 'minus';
        if (position === 'FOR') { posColor = 'var(--consensus)'; iconName = 'check'; }
        if (position === 'AGAINST') { posColor = 'var(--risk)'; iconName = 'x'; }
        if (position === 'REFRAME') { posColor = 'var(--reframe)'; iconName = 'git-branch'; }
        
        votesContainer.innerHTML += `
          <div class="agent-vote-row">
            <span style="font-weight:600;">${formatAgentName(name)}</span>
            <span style="color: ${posColor}; font-weight: 700; display: inline-flex; align-items: center; gap: 6px; font-size: 13px;">
              <i data-lucide="${iconName}" style="width:14px;height:14px;"></i> ${position}
            </span>
          </div>
        `;
      };

      v.council_vote_for.forEach(a => renderVote(a, 'FOR'));
      v.council_vote_against.forEach(a => renderVote(a, 'AGAINST'));
      v.council_vote_reframe.forEach(a => renderVote(a, 'REFRAME'));
      
      // Goal divergence
      if (v.conflict_report) {
        document.getElementById('vd-user-goal').textContent = v.conflict_report.user_goal;
        document.getElementById('vd-council-finding').textContent = v.conflict_report.council_finding;
        
        const alert = document.getElementById('vd-divergence-alert');
        const alertText = document.getElementById('vd-div-text');
        const alertIcon = document.getElementById('vd-div-icon');
        
        if (v.conflict_report.divergence_severity === 'HIGH') {
          alert.className = 'divergence-alert div-high';
          alertText.textContent = 'High Divergence: Council verdict directly contradicts user goal';
          alertIcon.setAttribute('data-lucide', 'alert-triangle');
        } else {
          alert.className = 'divergence-alert div-low';
          alertText.textContent = 'Low Divergence: Council matches user goal constraints';
          alertIcon.setAttribute('data-lucide', 'check-circle');
        }
      }

      if (v.hitl_required) {
        document.getElementById('hitl-reason-text').textContent = v.hitl_reason;
      }
      
      lucide.createIcons();
    }

    function incrementImpactMetrics() {
      // Simulate metrics updates
      const s = parseInt(document.getElementById('metric-sessions').textContent);
      document.getElementById('metric-sessions').textContent = s + 1;
    }

    function launchDemo(clientId, taskInput) {
      document.getElementById('intake-task').value = taskInput;
      document.getElementById('intake-client').value = clientId;
      document.getElementById('intake-stakes').value = clientId === 'yesmadam' ? 'HIGH' : 'STANDARD';
      
      const btn = document.getElementById('intake-submit-btn');
      btn.disabled = false;
      btn.innerHTML = 'Start Deliberation <i data-lucide="arrow-right"></i>';
      
      showIntakeModal();
    }

    // ─── Real SDK Methods ───
    async function loadVerdict(sessionId) {
      try {
        const resp = await client.records.list("verdicts", {
          filter: [{ field: "session_id", op: "eq", value: sessionId }]
        });
        
        if (!resp.items || resp.items.length === 0) {
          document.getElementById('verdict-empty').style.display = 'flex';
          document.getElementById('verdict-container').style.display = 'none';
          return;
        }
        
        document.getElementById('verdict-empty').style.display = 'none';
        document.getElementById('verdict-container').style.display = 'grid';
        
        const v = resp.items[0];
        
        // Verdict Header
        const vText = document.getElementById('vd-verdict-text');
        vText.textContent = v.verdict;
        vText.className = `verdict-large v-${v.verdict}`;
        document.getElementById('vd-reason').textContent = v.recommended_action || "Verdict reached by council deliberation.";
        
        // Confidence Gauge
        const cScore = v.confidence_score || 0;
        const pct = Math.round(cScore * 100);
        document.getElementById('vd-confidence-text').textContent = `${pct}%`;
        
        const gaugeFill = document.getElementById('vd-gauge-fill');
        const dashOffset = 408 - (408 * cScore);
        gaugeFill.style.strokeDasharray = `${408 - dashOffset} 408`;
        
        let cColor = '#f43f5e';
        let cLabel = 'Low Confidence';
        if (cScore >= 0.8) { cColor = '#10b981'; cLabel = 'High Confidence'; }
        else if (cScore >= 0.6) { cColor = '#f59e0b'; cLabel = 'Moderate Confidence'; }
        
        gaugeFill.style.stroke = cColor;
        document.getElementById('vd-confidence-label').textContent = cLabel;
        
        // Agent Votes Breakdown
        let forAgents = [], againstAgents = [], abstainAgents = [], reframeAgents = [];
        try { forAgents = typeof v.council_vote_for === 'string' ? JSON.parse(v.council_vote_for) : (v.council_vote_for || []); } catch(e){}
        try { againstAgents = typeof v.council_vote_against === 'string' ? JSON.parse(v.council_vote_against) : (v.council_vote_against || []); } catch(e){}
        try { abstainAgents = typeof v.council_vote_abstain === 'string' ? JSON.parse(v.council_vote_abstain) : (v.council_vote_abstain || []); } catch(e){}
        try { reframeAgents = typeof v.council_vote_reframe === 'string' ? JSON.parse(v.council_vote_reframe) : (v.council_vote_reframe || []); } catch(e){}
        
        const totalVotes = forAgents.length + againstAgents.length + abstainAgents.length + reframeAgents.length;
        const bar = document.getElementById('vd-vote-bar');
        bar.innerHTML = '';
        
        if (totalVotes > 0) {
          const forPct = Math.round((forAgents.length / totalVotes) * 100);
          const againstPct = Math.round((againstAgents.length / totalVotes) * 100);
          const reframePct = Math.round((reframeAgents.length / totalVotes) * 100);
          
          if (forAgents.length > 0) {
            bar.innerHTML += `<div class="vote-segment seg-for" style="width: ${forPct}%;">FOR</div>`;
          }
          if (againstAgents.length > 0) {
            bar.innerHTML += `<div class="vote-segment seg-against" style="width: ${againstPct}%;">AGAINST</div>`;
          }
          if (reframeAgents.length > 0) {
            bar.innerHTML += `<div class="vote-segment" style="width: ${reframePct}%; background: var(--reframe);">${reframeAgents.length} REFRAME</div>`;
          }
        } else {
          bar.innerHTML = '<div class="vote-segment" style="width: 100%; background: var(--text-muted);">0 VOTES</div>';
        }

        const votesContainer = document.getElementById('vd-agent-votes');
        votesContainer.innerHTML = '';
        const addVote = (agent, pos) => {
          let posColor = pos === 'FOR' ? 'var(--consensus)' : (pos === 'AGAINST' ? 'var(--risk)' : (pos === 'REFRAME' ? 'var(--reframe)' : 'var(--text-muted)'));
          let icon = pos === 'FOR' ? 'check' : (pos === 'AGAINST' ? 'x' : (pos === 'REFRAME' ? 'git-branch' : 'minus'));
          votesContainer.innerHTML += `
            <div class="agent-vote-row">
              <span>${formatAgentName(agent)}</span>
              <span style="color: ${posColor}; display: flex; align-items: center; gap: 6px; font-weight: 600; font-size: 13px;">
                <i data-lucide="${icon}" class="icon-sm"></i> ${pos}
              </span>
            </div>
          `;
        };
        forAgents.forEach(a => addVote(a, 'FOR'));
        againstAgents.forEach(a => addVote(a, 'AGAINST'));
        reframeAgents.forEach(a => addVote(a, 'REFRAME'));
        abstainAgents.forEach(a => addVote(a, 'ABSTAIN'));
        
        // Conflict Report
        if (v.conflict_report) {
          let cr = typeof v.conflict_report === 'string' ? JSON.parse(v.conflict_report) : v.conflict_report;
          document.getElementById('vd-user-goal').textContent = cr.user_goal || 'N/A';
          document.getElementById('vd-council-finding').textContent = cr.council_finding || 'N/A';
          
          const alert = document.getElementById('vd-divergence-alert');
          const alertText = document.getElementById('vd-div-text');
          const alertIcon = document.getElementById('vd-div-icon');
          if (cr.divergence_severity === 'HIGH') {
            alert.className = 'divergence-alert div-high';
            alertText.textContent = 'High Divergence: Council contradicts user goal';
            alertIcon.setAttribute('data-lucide', 'alert-triangle');
          } else {
            alert.className = 'divergence-alert div-low';
            alertText.textContent = 'Low Divergence: Council aligns with user goal';
            alertIcon.setAttribute('data-lucide', 'check-circle');
          }
        }
        
        if (v.hitl_required) {
          document.getElementById('hitl-reason-text').textContent = v.hitl_reason || "Escalation thresholds met.";
        }
        
        lucide.createIcons();
      } catch (err) {
        console.error("Error loading verdict:", err);
      }
    }

    async function submitHitlDecision() {
      const btn = document.getElementById('hitl-submit-btn');
      const decision = document.querySelector('input[name="hitl_decision"]:checked').value;
      const reason = document.getElementById('hitl-reason-input').value;
      
      btn.disabled = true;
      btn.innerHTML = 'Submitting Verdict Override... <i data-lucide="loader" class="icon-sm"></i>';
      lucide.createIcons({root: btn});
      
      if (activeSessionId.startsWith('sim-')) {
        // Simulation resolution
        setTimeout(() => {
          document.getElementById('hitl-form-container').innerHTML = `
            <div style="text-align: center; padding: 20px;">
              <i data-lucide="check-circle" style="color: var(--consensus); width: 48px; height: 48px; margin-bottom: 16px;"></i>
              <h3>Verdict Override Processed</h3>
              <p style="color: var(--text-muted); margin-top: 8px;">Decision recorded: <strong>${decision.toUpperCase()}</strong>. Target systems updated.</p>
            </div>
          `;
          lucide.createIcons();
          
          // Update sim session status
          const session = simSessions.find(s => s.id === activeSessionId);
          if (session) {
            session.status = 'done';
            updateSidebarSim(session);
          }
        }, 1200);
        return;
      }
      
      try {
        if (currentWorkflowRunId) {
          const podId = client.podId;
          await client.request('POST', `/pods/${podId}/workflow-runs/${currentWorkflowRunId}/form`, {
            body: {
              node_id: formNodeId || 'hitl_approval',
              inputs: { decision, decision_reason: reason }
            }
          });
        } else {
          await client.records.create("hitl_queue", {
            session_id: activeSessionId,
            status: "resolved",
            decision: decision,
            decision_reason: reason
          });
          await client.records.update("debate_sessions", activeSessionId, {
            status: decision === 'send_back' ? 'debating' : 'done'
          });
        }
        
        document.getElementById('hitl-form-container').innerHTML = `
          <div style="text-align: center; padding: 20px;">
            <i data-lucide="check-circle" style="color: var(--consensus); width: 48px; height: 48px; margin-bottom: 16px;"></i>
            <h3>Decision Recorded</h3>
            <p style="color: var(--text-muted); margin-top: 8px;">The pipeline has successfully processed your verdict override.</p>
          </div>
        `;
        lucide.createIcons();
      } catch (err) {
        console.error("Error submitting HITL:", err);
        btn.disabled = false;
        btn.innerHTML = 'Error. Try Again';
      }
    }

    async function findWorkflowRun(sessionId) {
      try {
        const podId = client.podId;
        const listResp = await client.request('GET', `/pods/${podId}/workflows/debate-pipeline/runs`);
        const waitingRuns = (listResp?.items || []).filter(run => run.status === 'WAITING');
        for (const summary of waitingRuns) {
          const detailResp = await client.request('GET', `/pods/${podId}/workflow-runs/${summary.id}`);
          const ctx = detailResp?.execution_context || {};
          if (JSON.stringify(ctx).includes(sessionId)) {
            currentWorkflowRunId = detailResp.id;
            formNodeId = detailResp.active_wait?.node_id || 'hitl_approval';
            break;
          }
        }
      } catch (err) {
        console.warn('Could not find workflow run:', err);
      }
    }

    function setupFeedSubscription(sessionId) {
      if (feedSubscription) {
        if (feedSubscription.close) feedSubscription.close();
        else clearTimeout(feedSubscription);
        feedSubscription = null;
      }
      
      const renderedMessageIds = new Set();
      let currentRound = -1;
      let pollTimer = null;
      let wsHandle = null;
      
      const renderBatch = (items) => {
        if (!items || items.length === 0) return;
        // Sort by created_at ascending to ensure chronological round rendering
        const sorted = [...items].sort((a, b) => {
          const tA = a.created_at ? new Date(a.created_at).getTime() : 0;
          const tB = b.created_at ? new Date(b.created_at).getTime() : 0;
          return tA - tB;
        });
        
        sorted.forEach(msg => {
          if (!msg.id) return;
          if (!renderedMessageIds.has(msg.id)) {
            renderedMessageIds.add(msg.id);
            renderMessageCardSDK(msg, currentRound);
            currentRound = parseInt(msg.round_number, 10);
            const feedView = document.getElementById('view-feed');
            feedView.scrollTop = feedView.scrollHeight;
          }
        });
      };
      
      const loadExisting = async () => {
        try {
          const resp = await client.records.list("debate_messages", {
            filter: [{ field: "session_id", op: "eq", value: sessionId }],
            sort: [{ field: "created_at", direction: "asc" }],
            limit: 100
          });
          if (resp.items) renderBatch(resp.items);
        } catch (err) {
          console.error("Initial load error:", err);
        }
      };
      
      try {
        wsHandle = client.datastore.watchChanges({
          table: "debate_messages",
          onChange: (frame) => {
            if (activeSessionId !== sessionId) return;
            const op = (frame.operation || frame.type || '').toLowerCase();
            if (op === 'insert' || op === 'create') {
              client.records.get("debate_messages", frame.record_id).then(msg => {
                if (msg.session_id !== sessionId) return;
                renderBatch([msg]);
              }).catch(() => {});
            }
          }
        });
      } catch (e) {
        console.warn("datastore.watchChanges initialization failed:", e);
      }

      // Always launch safe polling loop in parallel to guarantee updates
      loadExisting();
      startPollLoop();
      
      function startPollLoop() {
        if (pollTimer) return;
        const poll = async () => {
          if (activeSessionId !== sessionId) return;
          try {
            const resp = await client.records.list("debate_messages", {
              filter: [{ field: "session_id", op: "eq", value: sessionId }],
              sort: [{ field: "created_at", direction: "asc" }],
              limit: 100
            });
            if (resp.items) renderBatch(resp.items);
          } catch (err) {
            console.error("Poll error:", err);
          }
          pollTimer = setTimeout(poll, 2500);
        };
        pollTimer = setTimeout(poll, 1500);
      }

      // Return combined handle
      feedSubscription = {
        close: () => {
          if (wsHandle && wsHandle.close) {
            try { wsHandle.close(); } catch(e) {}
          }
          if (pollTimer) {
            clearTimeout(pollTimer);
            pollTimer = null;
          }
        }
      };
    }


    function renderMessageCardSDK(msg, currentRound) {
      const emptyState = document.getElementById('feed-empty');
      if (emptyState) emptyState.remove();
      
      const msgRound = parseInt(msg.round_number, 10);
      if (currentRound !== msgRound) {
        const div = document.createElement('div');
        div.className = 'round-divider';
        div.textContent = msgRound === 0 ? 'Phase: Pre-Mortem' : `Debate Round ${msgRound}`;
        feedContainer.appendChild(div);
      }
      
      const posClass = msgRound === 0 ? 'pos-PREMORTEM' : `pos-${msg.position || 'ABSTAIN'}`;
      const posLabel = msgRound === 0 ? 'PRE-MORTEM' : (msg.position || 'ABSTAIN');
      
      const card = document.createElement('div');
      card.className = `message-card ${posClass}`;
      card.innerHTML = `
        <div class="message-header">
          <div class="agent-info">
            <div class="agent-avatar"><i data-lucide="bot" class="icon"></i></div>
            <div class="agent-details">
              <span class="agent-name">${formatAgentName(msg.agent_name || msg.agent_id)}</span>
              <span class="agent-bias">${msg.reasoning_bias || 'Analyst'}</span>
            </div>
          </div>
          <div class="position-badge">${posLabel}</div>
        </div>
        <div class="message-body">${escapeHtml(msg.argument)}</div>
      `;
      
      feedContainer.appendChild(card);
      lucide.createIcons({ root: card });
    }

    function setupSessionPolling(sessionId) {
      if (sessionSubscription) clearTimeout(sessionSubscription);
      
      const pollSession = async () => {
        if (activeSessionId !== sessionId) return;
        try {
          const session = await client.records.get("debate_sessions", sessionId);
          updateStatusIndicator(session.status);
          
          if (session.status === 'verdict' || session.status === 'done' || session.status === 'hitl') {
            await loadVerdict(sessionId);
            
            if (session.status === 'hitl') {
              document.getElementById('hitl-form-container').style.display = 'block';
              tabs[2].click(); // Switch to verdict dashboard
              await findWorkflowRun(sessionId);
            }
          }
          
          if (session.status !== 'done' && session.status !== 'hitl' && session.status !== 'failed') {
            sessionSubscription = setTimeout(pollSession, 3000);
          }
        } catch (err) {
          console.error(err);
        }
      };
      pollSession();
    }

    // ─── Intake Form and Modal Handlers ───
    function showIntakeModal() {
      document.getElementById('intake-modal').classList.add('show');
      lucide.createIcons({root: document.getElementById('intake-modal')});
    }

    function hideIntakeModal() {
      document.getElementById('intake-modal').classList.remove('show');
    }

    async function submitIntake() {
      const taskInput = document.getElementById('intake-task').value.trim();
      const clientId = document.getElementById('intake-client').value.trim();
      const stakesLevel = document.getElementById('intake-stakes').value;

      if (!taskInput) {
        document.getElementById('intake-task').focus();
        return;
      }

      const btn = document.getElementById('intake-submit-btn');
      btn.disabled = true;
      btn.innerHTML = 'Assembling Council... <i data-lucide="loader" class="icon-sm"></i>';
      lucide.createIcons({root: btn});

      if (!lemmaConnected) {
        // Simulation mode session spawn
        setTimeout(() => {
          const newSessionId = `sim-custom-${Date.now()}`;
          const newSession = {
            id: newSessionId,
            client_id: clientId || 'demo',
            task_input: taskInput,
            user_goal: "Evaluate prompt input",
            stripped_task: `Raw prompt evaluated: ${taskInput}`,
            stakes_level: stakesLevel,
            status: 'pending'
          };
          
          // Generate mock messages for custom task
          simMessages[newSessionId] = [
            { round_number: 0, agent_name: "policy-analyst", reasoning_bias: "rule-following", position: "PREMORTEM", argument: `Pre-Mortem Analysis: Evaluating request "${taskInput}". A failure will occur if standard constraints are ignored without documenting exception rules.` },
            { round_number: 0, agent_name: "customer-advocate", reasoning_bias: "empathetic", position: "PREMORTEM", argument: "Pre-Mortem Analysis: A failure will occur if we override user preferences, degrading company metrics." },
            { round_number: 1, agent_name: "customer-advocate", reasoning_bias: "empathetic", position: "FOR", argument: "I vote FOR accommodating this custom request. We should prioritize resolving the customer issue directly." },
            { round_number: 1, agent_name: "policy-analyst", reasoning_bias: "rule-following", position: "AGAINST", argument: "I vote AGAINST. Standard rules state we must verify all criteria before taking action." },
            { round_number: 1, agent_name: "panchai-brain", reasoning_bias: "Moderator", position: "MODERATOR", argument: "Moderator Challenge: The council has an active conflict. Policy analyst demands verification, customer advocate demands immediate approval. Let's find common ground." },
            { round_number: 2, agent_name: "policy-analyst", reasoning_bias: "rule-following", position: "REFRAME", argument: "I REFRAME: I agree to approve if the customer passes a secondary security identity check." },
            { round_number: 2, agent_name: "customer-advocate", reasoning_bias: "empathetic", position: "FOR", argument: "I accept the security check. That bridges our concerns." }
          ];

          simVerdicts[newSessionId] = {
            session_id: newSessionId,
            verdict: "APPROVED",
            confidence_score: 0.81,
            council_vote_for: ["customer-advocate", "policy-analyst"],
            council_vote_against: [],
            council_vote_abstain: [],
            council_vote_reframe: [],
            conflict_report: {
              user_goal: "Execute user request",
              council_finding: "Approved conditional on standard security verification check.",
              divergence_severity: "LOW"
            },
            recommended_action: "Proceed with approval once identity check confirms tenant ownership.",
            hitl_required: false,
            hitl_reason: "High confidence consensus reached."
          };

          simSessions.unshift(newSession); // Add to start of list
          loadSimSessionsDropdown();
          
          hideIntakeModal();
          document.getElementById('intake-task').value = '';
          
          // Set active and run simulation
          sessionSelect.value = newSessionId;
          setActiveSession(newSessionId);
          
          // Switch to feed tab
          document.getElementById('tab-feed').click();
          
        }, 1000);
        return;
      }

      // SDK Mode
      try {
        const podId = client.podId;
        
        // 1. Create a run of the debate-pipeline workflow
        const runRes = await client.workflows.runs.create("debate-pipeline");
        const runId = runRes.id;
        
        // 2. Submit the form inputs to start execution of the workflow
        try {
          await client.workflows.runs.submitForm(runId, {
            node_id: "input_form",
            inputs: {
              task_input: taskInput,
              task_context: "{}"
            }
          });
        } catch (submitErr) {
          console.warn("submitForm returned or timed out (will attempt to poll session anyway):", submitErr);
        }

        // 3. Poll for the session ID created by goal_strip
        let newSession = null;
        for (let i = 0; i < 30; i++) {
          await new Promise(r => setTimeout(r, 500));
          const list = await client.records.list("debate_sessions", {
            sort: [{ field: "created_at", direction: "desc" }],
            limit: 5
          });
          newSession = (list.items || []).find(s => s.task_input === taskInput);
          if (newSession) break;
        }

        if (!newSession) {
          throw new Error("Deliberation started, but session record was not found in the database. Please select it from the dropdown.");
        }

        hideIntakeModal();
        document.getElementById('intake-task').value = '';
        await loadSessions();

        // Select the newly spawned session
        sessionSelect.value = newSession.id;
        setActiveSession(newSession.id);
        
        document.getElementById('tab-feed').click();
      } catch (err) {
        console.error('Error starting session in live mode:', err);
        btn.disabled = false;
        btn.innerHTML = 'Start Deliberation <i data-lucide="arrow-right"></i>';
        lucide.createIcons({root: btn});
        alert('Failed to initiate live deliberation: ' + (err.message || 'Unknown error'));
      }
    }

    // ─── Helpers ───
    function formatAgentName(id) {
      if (!id) return "Agent";
      return id.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    }
    
    function escapeHtml(unsafe) {
      return (unsafe||'').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    // Close modals on overlay clicks
    document.getElementById('intake-modal').addEventListener('click', function(e) {
      if (e.target === this) hideIntakeModal();
    });
    
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') hideIntakeModal();
    });

    // Start App
    initApp();
  