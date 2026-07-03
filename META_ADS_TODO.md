# Meta Ads Project — To-Do List

**Project**: Accelerated Rehab Therapy (ART) Meta Ads Campaign  
**Focus**: Shockwave therapy treatment ads targeting chronic pain patients  
**Timeline**: Next couple of weeks

---

## 🔧 Infrastructure Tasks

### LLM Provider Switcher Script
**Status**: Design phase  
**Priority**: Medium  
**Target Completion**: Tomorrow

**Task Description**:
Create a script that allows switching between OpenRouter (current model: glm-4.7-flash:latest) and Anthropic LLMs on demand.

**Project Location**: `/workspace/Dev/llm-provider-switcher/`

**Sub-tasks**:
- [ ] Investigate current model configuration (CLI, config files, env vars)
- [ ] Design switching logic and configuration structure
- [ ] Create `switch_to_anthropic.sh` script
- [ ] Create `switch_to_openrouter.sh` script  
- [ ] Test switching mechanism
- [ ] Add validation/error handling
- [ ] Document usage instructions

**Notes**:
- Script should update configuration files and restart agent session
- Should verify successful switch before completing
- Keep existing configurations as backups
- Document which config files are affected

**Estimated Time**: 30–60 minutes

---

## 📋 Project Overview

We are creating and producing Meta ads (Facebook/Instagram) for shockwave therapy treatment at ART clinics in Denver and Greeley.

**Key Objectives**:
- Generate qualified leads for shockwave therapy
- Target chronic pain patients (plantar fasciitis, tendon pain, etc.)
- Drive bookings to the 5 existing landing pages
- Track performance via Meta Pixel

**Current Status**: Landing pages are built, need ad creation, targeting, and campaign setup.

---

## 🔴 High Priority — Phase 1: Campaign Setup & Launch

### 1.1 Meta Pixel Activation
- [ ] Obtain Pixel ID from Meta Business Manager
- [ ] Add `META_PIXEL_ID` to `.env` file
- [ ] Deploy changes to production
- [ ] Test Pixel is firing (PageView + Lead events)
- [ ] Install Meta Pixel Helper Chrome extension for verification

### 1.2 Google Chat Integration
- [ ] Configure Google Chat API credentials in CloudPulse (currently using)
- [ ] Set up notification routing for new leads
- [ ] Create Chat workspace/channel for lead routing
- [ ] Test notification delivery

### 1.3 Campaign Structure Planning
- [ ] Define three-stage funnel (Cold → Warm → Hot traffic)
- [ ] Create audience targeting strategy for Denver/Greeley
- [ ] Set up budget allocation (70% Cold, 20% Warm, 10% Hot)
- [ ] Identify ideal ad placements (News Feed + Instagram Stories)

### 1.4 First Campaign Launch
- [ ] Create first campaign in Meta Ads Manager
- [ ] Set up ad sets for 3 locations (Denver, Greeley, both)
- [ ] Create initial ad creative (discovery-driven hooks)
- [ ] Set daily budget ($20–$40/day to start)
- [ ] Launch and monitor first 24–48 hours

---

## 🟡 Medium Priority — Phase 2: Ad Creative Development

### 2.1 Cold Traffic Ads (70% of budget)
- [ ] Create 5–10 discovery-driven ad hooks
- [ ] Design ad images (or use placeholder: `landing_shockwave_denver.html` images)
- [ ] Write primary text for each ad
- [ ] Test Headline A/B (Current vs. Alternative)
- [ ] Test CTA button text variations

**Discovery Hook Ideas** (from SHOCKWAVE.md):
- "Some aches don't quit..."
- Movement-focused discovery messaging
- Lifestyle challenge hooks

### 2.2 Warm Traffic Retargeting (20% of budget)
- [ ] Create credibility-focused ads
- [ ] Write clinic approach messaging
- [ ] Design testimonial-style ads
- [ ] Set up audience segments
- [ ] Launch retargeting campaigns

### 2.3 Hot Traffic Closers (10% of budget)
- [ ] Create availability-based ads
- [ ] Write limited slots messaging
- [ ] Add urgency/scarcity elements
- [ ] Test urgency CTAs

### 2.4 A/B Testing Framework
- [ ] Identify key metrics (CTR, CPC, Cost Per Lead)
- [ ] Set up testing schedule (bi-weekly deep dives)
- [ ] Create ad rotation strategy
- [ ] Document winning creative patterns

---

## 🟢 Lower Priority — Phase 3: Optimization & Expansion

### 3.1 Performance Analysis
- [ ] Review first 2 weeks of campaign data
- [ ] Identify top-performing ads/location/conditions
- [ ] Calculate actual Cost Per Lead (CPL)
- [ ] Determine optimal budget allocation
- [ ] Document lessons learned

### 3.2 Scaling Winners
- [ ] Increase budget on top-performing campaigns
- [ ] Expand to additional conditions (shoulder, knee, etc.)
- [ ] Test new ad formats (Reels, Stories, Carousel)
- [ ] Expand targeting radius if needed

### 3.3 Advanced Features
- [ ] Add Multi-Touch Conversion Attribution
- [ ] Implement Lookalike audiences
- [ ] Set up automated bidding strategies
- [ ] Create custom audiences based on landing page behavior

---

## 📸 Ad Creative Assets Needed

### Images
- [ ] Clinic photo/logo (replace placeholder in all landing pages)
- [ ] Shockwave device professional image
- [ ] Professional before/after slider images (optional)
- [ ] Lifestyle images showing pain-free activity

### Video Content
- [ ] 60-second general shockwave education video
- [ ] 30-second plantar fasciitis specific video
- [ ] 60-second elbow/golfers tennis specific video
- [ ] 60-second shoulder pain specific video

### Copy Templates
- [ ] 10 headline + subheadline combinations (already have 4 in SHOCKWAVE.md)
- [ ] 20 short ad hooks (already have 15+ in SHOCKWAVE.md)
- [ ] FAQ section content for landing pages
- [ ] Objection handling scripts for front desk

---

## 📊 Tracking & Analytics

### Meta Pixel Setup
- [ ] Verify PageView event firing on all 5 landing pages
- [ ] Confirm Lead event firing on /thank-you page
- [ ] Set up Custom Conversions in Events Manager
- [ ] Configure Cross-domain tracking if needed

### Analytics Dashboard
- [ ] Create Google Sheets dashboard for tracking
- [ ] Set up monthly reporting automation
- [ ] Track by: campaign, ad set, ad, location, condition
- [ ] Monitor: impressions, clicks, CTR, CPC, CPL, conversions

### Goal Tracking
- [ ] Define success metrics (e.g., 5 leads/day minimum)
- [ ] Set up automated reporting
- [ ] Create performance review schedule (bi-weekly)

---

## 💰 Budget Planning

### Initial Budget
- [ ] Set daily budget: $20–$40/start → Scale after 2 weeks
- [ ] Allocate by funnel stage: 70% Cold, 20% Warm, 10% Hot
- [ ] Separate budgets for Denver vs. Greeley locations

### Expected ROI
- [ ] Calculate break-even for $99 trial offer
- [ ] Estimate conversion rate to package purchases
- [ ] Determine monthly revenue targets based on lead volume

---

## ✅ Completion Checklist

### Week 1
- [ ] Meta Pixel activated
- [ ] Google Chat setup
- [ ] Campaign structure planned
- [ ] First campaign launched
- [ ] Initial ad creative created

### Week 2
- [ ] A/B testing framework in place
- [ ] Performance analysis complete
- [ ] Winners identified and scaled
- [ ] Budget optimized
- [ ] Documentation complete

---

## 📝 Notes & Resources

**Key Documents**:
- LANDING_PAGES.md — Landing page structure and URLs
- SHOCKWAVE.md — Comprehensive shockwave program guide and marketing copy
- RECOMMENDATIONS.md — Site review and improvements
- README.md — Project setup and deployment

**Important Links**:
- Meta Business Manager: https://business.facebook.com
- Events Manager: https://business.facebook.com/your-id/insights
- CloudPulse: https://app.cloudpulse.ai

**Team Members**:
- ART Front Desk / Case Manager
- Clinic Leadership (billing approval)
- External AI Assistant (Claude/GPT for copy generation)

---

*Last Updated: 2026-05-20*
*Next Review: 2026-06-03*

### LLM Provider Switcher Script
**Status**: ✅ Design Phase Complete  
**Priority**: Medium  
**Target Completion**: Tomorrow (when you activate)

**Task Description**:
Create a script that allows switching between OpenRouter (current model: glm-4.7-flash:latest) and Anthropic LLMs on demand.

**Project Location**: `/workspace/Dev/llm-provider-switcher/`

**Sub-tasks**:
- [x] Design comprehensive architecture (✅ COMPLETE)
- [x] Identify configuration files and structure (✅ COMPLETE)
- [x] Map switching logic (✅ COMPLETE)
- [x] Document implementation plan (✅ COMPLETE)
- [ ] Investigate actual configuration file locations (⏸️ Pending from your environment)
- [ ] Write switch_provider.sh script (⏸️ Pending user activation)
- [ ] Write helper scripts (⏸️ Pending user activation)
- [ ] Test switching mechanism (⏸️ Pending user activation)

**Notes**:
- Design architecture documented in `/workspace/Dev/llm-provider-switcher/docs/DESIGN.md`
- Investigation notes in `/workspace/Dev/llm-provider-switcher/docs/INVESTIGATION_NOTES.md`
- Waiting for your confirmation and configuration details before implementation
- Script will auto-discover configuration files and handle restarts

**Estimated Time**: 30–60 minutes (pending implementation)

---

### For Tomorrow — Configuration Investigation (Your Action Required)

Please check the following from your actual environment:

1. **Check for config files**:
   ```bash
   ls -la ~/.config/hermes/config.json ~/.anthropic/config ~/.env
   ```

2. **Check environment variables**:
   ```bash
   env | grep -i "llm\|model\|openrouter\|anthropic"
   ```

3. **Determine restart requirement**: Try switching manually if possible

4. **Find API key locations**: Where are they stored (.env, env vars, etc.)?

**Your findings will help refine the script implementation.**

---

*Last Updated: 2026-05-20*
*Next Review: Tomorrow (user activation)*


---

## 📂 LLM Provider Switcher — Project Structure

**Status**: ✅ Design Phase Complete  
**Priority**: Medium  
**Location**: `/workspace/Dev/llm-provider-switcher/`

**Project Structure**:
```
llm-provider-switcher/
├── 📁 docs/
│   ├── 📄 DESIGN.md                      ✅ Architecture & implementation plan
│   ├── 📄 INVESTIGATION_NOTES.md         ✅ Configuration discovery framework
│   └── 📄 USAGE.md                       🔜 User instructions
├── 📄 switch_provider.sh                 🔜 Main switching script
├── 📄 verify_provider.sh                 🔜 Verification script
├── 📄 backup_config.sh                   🔜 Backup functionality
├── 📄 restore_config.sh                  🔜 Rollback capability
└── 📁 backups/                           🔜 Config backups
```

**What's Complete (Tonight)**:
- ✅ Comprehensive design document created
- ✅ Configuration architecture defined
- ✅ Script structure documented
- ✅ Switching logic mapped
- ✅ Implementation plan outlined
- ✅ Investigation framework established
- ✅ Auto-discovery strategy defined

**What's Pending (Tomorrow)**:
- ⏸️ Your configuration investigation (check actual config locations)
- ⏸️ Implementation when you activate
- 🔜 User documentation (USAGE.md)
- 🔜 Script testing

---

*Last Updated: 2026-05-20*
*Next Review: Tomorrow (when you activate)*
