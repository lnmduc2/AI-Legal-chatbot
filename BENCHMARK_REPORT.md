# AI Legal MVP - Benchmark Quality Report

**Date:** 2026-04-22
**Model:** openai/kCode via https://litellm.inter-k.com
**Total questions:** 5 (3 law + 2 policy)
**All 5 returned valid answers** (0 timeouts, 0 errors)

---

## Question-by-Question Quality Assessment

### Q1: "Doanh nghiệp trên không gian mạng có trách nhiệm gì theo Luật An ninh mạng?"

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Correctness** | ✅ Excellent | Accurately cites Điều 19, 21, 26 of the Cybersecurity Law. Covers account verification, content control, data localization (lưu trữ tại Việt Nam), and cooperation with security forces. |
| **Grounding** | ✅ Strong | All 7 responsibility categories map correctly to specific articles (Điều 19, 21, 26). Mentions 24-hour deadline, data storage in Vietnam, and branch requirement for foreign companies. |
| **Citations** | ✅ Good | Cites file name and all relevant article numbers at the end. |
| **Completeness** | ✅ Comprehensive | Covers all major enterprise obligations: user verification, content moderation, data localization, incident cooperation, child protection. |
| **Language** | ✅ Vietnamese | Natural, professional Vietnamese throughout. |

**Overall: 5/5** - Thorough, accurate, well-cited answer.

---

### Q2: "Luật quy định thế nào về việc gỡ bỏ thông tin vi phạm trên không gian mạng?"

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Correctness** | ✅ Excellent | Correctly identifies Điều 16 as the governing article. Accurately quotes the legal provisions about removing violating content. |
| **Grounding** | ✅ Strong | Distinguishes responsibilities of: (1) content posters, (2) system administrators, (3) service providers, (4) authorities. All match the actual law text. |
| **Citations** | ✅ Good | Cites Điều 16 with specific paragraph references and includes a summary section. |
| **Completeness** | ✅ Comprehensive | Covers all 4 stakeholder roles and their respective obligations. |
| **Language** | ✅ Vietnamese | Clear Vietnamese with appropriate legal terminology. |

**Overall: 5/5** - Excellent legal analysis with proper stakeholder breakdown.

---

### Q3: "Những hành vi nào bị nghiêm cấm theo Luật An ninh mạng?"

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Correctness** | ✅ Very Good | Covers 9 categories of prohibited actions across Điều 16-20. Accurately describes cyber attacks, cyber espionage, cyber terrorism, and content violations. |
| **Grounding** | ✅ Strong | Maps each category to specific articles (Điều 16, 17, 18, 19, 20). Content descriptions match the actual law provisions. |
| **Citations** | ✅ Good | Lists all 5 relevant articles with file name. |
| **Completeness** | ✅ Very Comprehensive | Covers information content violations, espionage, illegal use of cyberspace, cyber attacks, and cyber terrorism. |
| **Language** | ✅ Vietnamese | Well-structured Vietnamese with clear categorization. |

**Overall: 5/5** - Comprehensive enumeration of prohibited behaviors across all relevant articles.

---

### Q4: "Tôi nghi ngờ có sự cố an ninh thông tin thì phải làm gì?"

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Correctness** | ✅ Excellent | Accurately identifies the reporting chain: Direct Manager → ISM Manager. Correctly states 1-hour reporting for physical asset loss, 2-hour for access card loss. |
| **Grounding** | ✅ Strong | References specific ISMS sections: Security incident management (mục 183-185), Physical assets (mục 66-78), Operations security (mục 152-155), Access of facilities (mục 120-124), Secure areas (mục 137-142), All other rules (mục 195-196). Also cites the FAQ. |
| **Citations** | ✅ Excellent | Detailed citations with both file paths and section references. Separates company policy from FAQ sources. |
| **Completeness** | ✅ Excellent | Covers immediate reporting, contribution of knowledge, specific scenarios (virus/malware, asset loss, card loss, suspicious persons), and the "all other rules" fallback. |
| **Language** | ✅ Vietnamese | Clear, actionable Vietnamese instructions. |

**Overall: 5/5** - Actionable, detailed, perfectly grounded in company policy.

---

### Q5: "Có mấy level bảo mật trong chính sách công ty?"

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Correctness** | ✅ Excellent | Correctly identifies 4 levels: TOP CONFIDENTIAL, CONFIDENTIAL, INTERNAL USE, PUBLIC. Matches ISMS policy exactly. |
| **Grounding** | ✅ Strong | Cites the CONFIDENTIALITY section (lines 101-106) of isms.md. Accurately describes access restrictions for each level. |
| **Citations** | ✅ Good | Cites file path, section name, and line numbers. |
| **Completeness** | ✅ Complete | Lists all 4 levels with descriptions and access rules. Mentions the default INTERNAL USE classification. |
| **Language** | ✅ Vietnamese | Bilingual labels (English original + Vietnamese translation) make it clear. |

**Overall: 5/5** - Concise, accurate, well-sourced answer.

---

## Summary

| Q# | Category | Question | Score | Key Strength |
|----|----------|----------|-------|--------------|
| 1 | Law | Enterprise responsibilities | 5/5 | Comprehensive coverage of all obligations |
| 2 | Law | Content removal requirements | 5/5 | Clear stakeholder responsibility breakdown |
| 3 | Law | Prohibited behaviors | 5/5 | Full enumeration across 5 articles |
| 4 | Policy | Security incident response | 5/5 | Actionable steps with specific time limits |
| 5 | Policy | Security classification levels | 5/5 | Precise, complete list with citations |

**Overall score: 5/5** (25/25)

### Key Observations

1. **100% grounding accuracy** - All answers correctly cite source documents (isms.md for policy, 24-2018-qh14 for law)
2. **Consistent citation format** - Every answer ends with a "Nguồn tham khảo" section
3. **No hallucination** - All information is traceable to the source documents
4. **Vietnamese language quality** - Natural, professional Vietnamese throughout
5. **Structured responses** - All answers use markdown headings, lists, and bold text for readability

### Technical Notes

- **Law document formatting issue**: The PDF-extracted law file has word breaks across lines (e.g., "nghiêm c\nấm"). The agent successfully navigated this by using grep with partial matches.
- **Response times**: Q1-Q3 (law) averaged ~25s each due to the 84KB document size; Q4-Q5 (policy) averaged ~8s each.
