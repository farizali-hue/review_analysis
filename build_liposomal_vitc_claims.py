import csv
import json
import re
from pathlib import Path


INPUT_CSV = Path(r"D:\codex_variation_analysis\outputs\liposomal_vitc_claims.csv")
SECTIONS_JSON = Path(r"D:\analysis\liposomal_vitc_sections.json")
OUT_ASIN = Path(r"D:\analysis\liposomal_vitc_claims_formalized_with_evidence.csv")
OUT_CLAIMS = Path(r"D:\analysis\liposomal_vitc_claims_claim_level_evidence.csv")
OUT_ORDER = Path(r"D:\analysis\liposomal_vitc_claim_order.csv")


CATEGORY_ORDER = [
    "Health/Benefit Claims",
    "Certification Claims",
    "Nutritional Claims",
    "Other Claims",
]

CLAIM_ORDER = {
    "Health/Benefit Claims": [
        "Immune Support",
        "Common Illness Defense",
        "White Blood Cell Support",
        "Antioxidant Support",
        "Enhanced Absorption",
        "Fast Absorption",
        "Enhanced Bioavailability",
        "Digestive Comfort",
        "Digestive Health Support",
        "General Wellness Support",
        "Overall Well-Being Support",
        "Cellular Health Support",
        "Cellular Defense",
        "Cellular Vitality",
        "Collagen Production Support",
        "Skin Health Support",
        "Youthful Complexion Support",
        "Joint Support",
        "Joint/Connective Tissue Support",
        "Cartilage/Tendon/Ligament Support",
        "Bone Health Support",
        "Bone Density Support",
        "Teeth/Gum Health Support",
        "Gum Health Support",
        "Brain/Cognitive Health Support",
        "Mental Acuity Support",
        "Nerve Support",
        "Heart/Cardiovascular Support",
        "Eye Support",
        "Blood Circulation Support",
        "Blood Pressure Control",
        "Respiratory Support",
        "Calcium Absorption Support",
        "Iron Absorption Support",
        "Folic Acid Utilization Support",
        "Mood Support",
        "Energy Support",
        "Muscle Recovery Support",
        "Recovery Support",
        "Vitality Support",
        "Balanced Nutrition Support",
        "Anti-Aging Support",
        "Wrinkle Support",
        "Deficiency Protection",
        "Daily Wellness Support",
        "Resilience Support",
    ],
    "Certification Claims": [
        "Non-GMO Project Verified",
        "Non-GMO",
        "Gluten-Free",
        "Soy-Free",
        "Dairy-Free",
        "Sugar-Free",
        "Preservative-Free",
        "Dye-Free",
        "No Artificial Ingredients",
        "No Artificial Flavors",
        "No Toxic Additives",
        "No Harmful Chemicals",
        "No Fillers",
        "Free From Additives",
        "No Animal Byproducts",
        "No Eggs",
        "No Gelatin",
        "No Caffeine",
        "No Hormones",
        "Vegan",
        "Vegetarian",
        "Vegetarian-Friendly",
        "Plant-Based",
        "Keto",
        "Halal",
        "Organic Ingredients",
        "100% Natural",
        "Made in USA",
        "US Manufacturing Facility",
        "Globally Sourced Ingredients",
        "GMP-Certified/Compliant Facility",
        "USP Good Manufacturing Practices",
        "NSF-Approved",
        "ISO",
        "Third-Party/Lab Tested",
        "Independently Verified",
        "Heavy Metal Tested",
        "Laboratory Quality Control",
        "Quality/Purity Tested",
        "Strict Quality Standards",
        "Premium Quality Ingredients",
        "Small Business",
    ],
    "Nutritional Claims": [
        "Vitamin C",
        "Liposomal Vitamin C",
        "LipoQuil-C",
        "Fat-Soluble Vitamin C",
        "Buffered Vitamin C",
        "High Dose/High Potency Vitamin C",
        "Vitamin C 1,000 mg per serving",
        "Vitamin C 1,500 mg per serving",
        "Vitamin C 1,650 mg",
        "Vitamin C 1,700 mg per serving",
        "Liposomal Vitamin C 1,400 mg",
        "Liposomal Vitamin C 1,450 mg",
        "Over 1,000 mg Vitamin C",
        "Liposomal Complex 400 mg",
        "Sunflower Oil and Lecithin Phospholipids 50 mg",
        "Ascorbic Acid",
        "Ascorbyl Palmitate",
        "Ascorbyl Oleate",
        "Calcium Ascorbate",
        "Sodium Ascorbate",
        "Cetyl Ascorbate",
        "Palmitic Acid",
        "Organic Acerola Cherry",
        "Organic Camu Camu",
        "Whole Food Vitamin C",
        "Sunflower Lecithin",
        "Sunflower Oil",
        "Phospholipid",
        "Phospholipid Complex",
        "Phosphatidylcholine",
        "Coconut Oil/MCT",
        "Medium Chain Triglycerides",
        "Capsule Form",
        "Vegetable Capsules",
        "Vegan Capsules",
        "2-Capsule Serving",
        "Dietary Supplement",
        "Unflavored",
        "Orange Flavor",
        "120 Capsules",
        "180 Capsules",
        "200 Capsules",
        "90 Servings",
        "100-Day Supply",
    ],
    "Other Claims": [
        "Easy to Swallow",
        "Easy to Take",
        "Taste-Friendly",
        "Tasteless Formula",
        "No Bad Taste",
        "No Strong Aftertaste",
        "No Smell",
        "No Refrigeration Needed",
        "Shelf-Stable",
        "Long Shelf Life",
        "3-Month Supply",
        "90-Day Supply",
        "100-Day Supply",
        "120 Capsules",
        "180 Capsules",
        "200 Capsules",
        "90 Servings",
        "Clean Label/Purity",
        "Premium/Pure Ingredients",
        "Pure and Safe Ingredients",
        "No Unnecessary Fillers or Allergens",
        "No Rice Flour",
        "No Magnesium Stearate",
        "Strict Quality Control",
        "Batch Tested",
        "Doctor-Formulated",
        "Doctor-Recommended",
        "Satisfaction Guarantee",
        "Trustworthy Service",
        "Dedicated Customer Care",
        "Effective Formula",
        "Bioavailable Formula",
        "Affordable Compared to Liquid Form",
        "Convenient Capsules",
        "Transparency/List Every Ingredient",
        "Capsule Color/Scent May Vary",
        "Allergen Warning: Contains Tree Nuts/Coconuts",
        "Small Business",
        "No Sugar/No Junk",
    ],
}


CLAIMS = {
    "B00JFF48I6": {
        "Health/Benefit Claims": [
            "Immune Support", "Antioxidant Support", "Enhanced Absorption", "Enhanced Bioavailability",
            "Digestive Comfort", "Cellular Health Support", "Collagen Production Support",
            "Brain/Cognitive Health Support", "Heart/Cardiovascular Support", "Eye Support",
            "Vitality Support", "Daily Wellness Support",
        ],
        "Certification Claims": [
            "Non-GMO Project Verified", "Non-GMO", "Gluten-Free", "Soy-Free",
        ],
        "Nutritional Claims": [
            "Vitamin C", "Liposomal Vitamin C", "Vitamin C 1,000 mg per serving", "Ascorbic Acid",
            "Sunflower Lecithin", "Sunflower Oil", "Medium Chain Triglycerides", "Capsule Form",
            "Dietary Supplement", "Unflavored", "180 Capsules", "90 Servings",
        ],
        "Other Claims": [
            "Easy to Swallow", "3-Month Supply", "180 Capsules", "90 Servings", "Clean Label/Purity",
            "No Unnecessary Fillers or Allergens",
        ],
    },
    "B0BT1QB131": {
        "Health/Benefit Claims": [
            "Immune Support", "Antioxidant Support", "Enhanced Absorption", "Enhanced Bioavailability",
            "Digestive Comfort", "Collagen Production Support",
            "Cartilage/Tendon/Ligament Support", "Bone Density Support", "Brain/Cognitive Health Support",
            "Blood Circulation Support", "Calcium Absorption Support", "Iron Absorption Support",
            "Mood Support", "Anti-Aging Support", "Wrinkle Support",
        ],
        "Certification Claims": [
            "Non-GMO", "GMP-Certified/Compliant Facility", "NSF-Approved",
            "Third-Party/Lab Tested", "US Manufacturing Facility", "Quality/Purity Tested", "Small Business",
        ],
        "Nutritional Claims": [
            "Vitamin C", "Liposomal Vitamin C", "LipoQuil-C", "Fat-Soluble Vitamin C",
            "High Dose/High Potency Vitamin C", "Vitamin C 1,000 mg per serving", "Ascorbic Acid",
            "Sunflower Lecithin", "Phospholipid", "Phosphatidylcholine", "Capsule Form",
            "Unflavored", "120 Capsules",
        ],
        "Other Claims": ["Batch Tested", "120 Capsules", "Small Business"],
    },
    "B088YG3YRL": {
        "Health/Benefit Claims": [
            "Immune Support", "Antioxidant Support", "Enhanced Absorption",
            "Collagen Production Support", "Joint Support", "Bone Health Support", "Energy Support",
            "Brain/Cognitive Health Support", "Cellular Health Support", "Deficiency Protection",
        ],
        "Certification Claims": [
            "Non-GMO", "Gluten-Free", "Soy-Free", "Dairy-Free", "Sugar-Free", "Preservative-Free",
            "Vegan", "Vegetarian-Friendly", "Keto", "Made in USA", "GMP-Certified/Compliant Facility",
            "Third-Party/Lab Tested", "Independently Verified", "Small Business",
        ],
        "Nutritional Claims": [
            "Vitamin C", "Liposomal Vitamin C", "Liposomal Vitamin C 1,400 mg",
            "Vitamin C 1,000 mg per serving", "Liposomal Complex 400 mg",
            "High Dose/High Potency Vitamin C", "Coconut Oil/MCT", "Medium Chain Triglycerides",
            "Sunflower Lecithin", "Phosphatidylcholine", "Capsule Form", "Vegan Capsules",
            "Unflavored", "120 Capsules",
        ],
        "Other Claims": [
            "Tasteless Formula", "Easy to Swallow", "120 Capsules",
            "Allergen Warning: Contains Tree Nuts/Coconuts", "Small Business",
        ],
    },
    "B086D3TN83": {
        "Health/Benefit Claims": [
            "Immune Support", "Antioxidant Support", "Enhanced Absorption", "Enhanced Bioavailability",
            "Digestive Comfort", "Overall Well-Being Support", "Collagen Production Support",
            "Brain/Cognitive Health Support", "Heart/Cardiovascular Support",
            "Calcium Absorption Support", "Iron Absorption Support", "Gum Health Support",
            "Anti-Aging Support",
        ],
        "Certification Claims": [
            "Non-GMO", "No Fillers", "Free From Additives", "Vegan", "Plant-Based",
            "Organic Ingredients", "Made in USA", "GMP-Certified/Compliant Facility",
            "Third-Party/Lab Tested", "Heavy Metal Tested", "Strict Quality Standards", "Small Business",
        ],
        "Nutritional Claims": [
            "Vitamin C", "Liposomal Vitamin C", "High Dose/High Potency Vitamin C",
            "Vitamin C 1,500 mg per serving", "Ascorbic Acid", "Organic Acerola Cherry",
            "Organic Camu Camu", "Whole Food Vitamin C", "Sunflower Lecithin",
            "Phosphatidylcholine", "Capsule Form", "180 Capsules",
        ],
        "Other Claims": [
            "No Rice Flour", "No Magnesium Stearate", "Capsule Color/Scent May Vary", "180 Capsules",
            "Strict Quality Control", "Small Business",
        ],
    },
    "B086GK9SWD": {
        "Health/Benefit Claims": [
            "Immune Support", "Common Illness Defense", "White Blood Cell Support", "Antioxidant Support",
            "Enhanced Absorption", "Enhanced Bioavailability", "Digestive Comfort",
            "Overall Well-Being Support", "Collagen Production Support", "Skin Health Support",
            "Joint/Connective Tissue Support", "Bone Health Support", "Teeth/Gum Health Support",
            "Brain/Cognitive Health Support", "Mental Acuity Support", "Nerve Support",
            "Heart/Cardiovascular Support", "Blood Circulation Support", "Respiratory Support",
            "Iron Absorption Support", "Energy Support",
        ],
        "Certification Claims": [
            "Non-GMO", "Soy-Free", "Gluten-Free", "Dairy-Free", "No Fillers", "Free From Additives",
            "No Animal Byproducts", "No Eggs", "No Gelatin", "No Caffeine", "Vegan", "Vegetarian",
            "Organic Ingredients", "Made in USA", "GMP-Certified/Compliant Facility",
            "USP Good Manufacturing Practices", "Third-Party/Lab Tested", "No Harmful Chemicals",
            "No Hormones", "Doctor-Formulated", "Doctor-Recommended", "Small Business",
        ],
        "Nutritional Claims": [
            "Vitamin C", "Liposomal Vitamin C", "Fat-Soluble Vitamin C", "Buffered Vitamin C",
            "Vitamin C 1,500 mg per serving", "Liposomal Vitamin C 1,450 mg",
            "Sunflower Oil and Lecithin Phospholipids 50 mg", "Ascorbic Acid",
            "Ascorbyl Palmitate", "Sodium Ascorbate", "Palmitic Acid", "Sunflower Lecithin",
            "Phospholipid Complex", "Vegetable Capsules", "200 Capsules", "100-Day Supply",
        ],
        "Other Claims": [
            "Easy to Take", "Taste-Friendly", "No Smell", "Satisfaction Guarantee",
            "100-Day Supply", "200 Capsules", "Strict Quality Control",
            "Doctor-Formulated", "Doctor-Recommended", "Small Business",
        ],
    },
    "B07K8QLGHN": {
        "Health/Benefit Claims": [
            "Immune Support", "Antioxidant Support", "Enhanced Absorption", "Enhanced Bioavailability",
            "Digestive Comfort", "Overall Well-Being Support", "Brain/Cognitive Health Support",
            "Heart/Cardiovascular Support", "Blood Circulation Support", "Blood Pressure Control",
            "Digestive Health Support", "Bone Health Support", "Mood Support",
            "Muscle Recovery Support", "Recovery Support", "Anti-Aging Support",
            "Wrinkle Support", "Youthful Complexion Support",
        ],
        "Certification Claims": [
            "Non-GMO", "Gluten-Free", "Soy-Free", "Dairy-Free", "No Artificial Flavors",
            "No Toxic Additives", "Vegan", "Vegetarian", "100% Natural", "Made in USA",
            "GMP-Certified/Compliant Facility", "Third-Party/Lab Tested", "Small Business",
        ],
        "Nutritional Claims": [
            "Vitamin C", "Liposomal Vitamin C", "Fat-Soluble Vitamin C",
            "High Dose/High Potency Vitamin C", "Vitamin C 1,650 mg",
            "Over 1,000 mg Vitamin C", "Capsule Form", "Unflavored", "180 Capsules",
        ],
        "Other Claims": ["Premium/Pure Ingredients", "180 Capsules", "Small Business"],
    },
    "B07DH1ZJZ9": {
        "Health/Benefit Claims": [
            "Immune Support", "Antioxidant Support", "Enhanced Absorption",
            "Enhanced Bioavailability", "General Wellness Support", "Collagen Production Support",
            "Heart/Cardiovascular Support", "Vitality Support", "Balanced Nutrition Support",
        ],
        "Certification Claims": [
            "Non-GMO", "Gluten-Free", "Soy-Free", "Dairy-Free", "No Artificial Ingredients",
            "Preservative-Free", "Vegan", "Vegetarian", "Plant-Based", "Made in USA",
            "GMP-Certified/Compliant Facility", "Third-Party/Lab Tested", "Small Business",
        ],
        "Nutritional Claims": [
            "Vitamin C", "Liposomal Vitamin C", "Fat-Soluble Vitamin C",
            "Vitamin C 1,700 mg per serving",
            "Capsule Form", "Orange Flavor", "180 Capsules",
        ],
        "Other Claims": [
            "Long Shelf Life", "Pure and Safe Ingredients", "Premium/Pure Ingredients",
            "No Sugar/No Junk", "180 Capsules", "Small Business",
        ],
    },
    "B07DR13XSX": {
        "Health/Benefit Claims": [
            "Immune Support", "Antioxidant Support", "Enhanced Absorption", "Enhanced Bioavailability",
            "Digestive Comfort", "Overall Well-Being Support", "Collagen Production Support",
            "Skin Health Support", "Teeth/Gum Health Support", "Iron Absorption Support",
            "Folic Acid Utilization Support", "Energy Support", "Vitality Support",
        ],
        "Certification Claims": [
            "Non-GMO", "Gluten-Free", "Vegan", "Vegetarian", "Halal", "Premium Quality Ingredients",
        ],
        "Nutritional Claims": [
            "Vitamin C", "Liposomal Vitamin C", "Fat-Soluble Vitamin C", "Buffered Vitamin C",
            "Vitamin C 1,700 mg per serving", "Ascorbic Acid", "Ascorbyl Palmitate",
            "Ascorbyl Oleate", "Calcium Ascorbate", "Cetyl Ascorbate", "Palmitic Acid",
            "Sunflower Lecithin", "Phosphatidylcholine", "Dry Liposomal Complex",
            "Capsule Form", "Unflavored", "200 Capsules",
        ],
        "Other Claims": [
            "No Bad Taste", "No Strong Aftertaste", "No Refrigeration Needed", "Shelf-Stable",
            "Affordable Compared to Liquid Form", "Convenient Capsules",
            "Transparency/List Every Ingredient", "200 Capsules",
        ],
    },
    "B0F4XPWTMR": {
        "Health/Benefit Claims": [
            "Immune Support", "Antioxidant Support", "Enhanced Absorption", "Enhanced Bioavailability",
            "Digestive Comfort", "Overall Well-Being Support", "Cellular Defense",
            "Cellular Vitality", "Skin Health Support", "Energy Support", "Vitality Support",
            "Resilience Support",
        ],
        "Certification Claims": [
            "Non-GMO", "Gluten-Free", "Soy-Free", "Dye-Free", "Vegan", "Made in USA",
            "Globally Sourced Ingredients", "GMP-Certified/Compliant Facility", "ISO",
            "Laboratory Quality Control", "Strict Quality Standards",
        ],
        "Nutritional Claims": [
            "Vitamin C", "Liposomal Vitamin C", "Fat-Soluble Vitamin C",
            "Vitamin C 1,700 mg per serving", "Ascorbic Acid", "Ascorbyl Palmitate",
            "Sunflower Lecithin", "Vegetable Capsules", "2-Capsule Serving", "180 Capsules",
        ],
        "Other Claims": [
            "90-Day Supply", "180 Capsules", "Premium/Pure Ingredients",
            "Trustworthy Service", "Dedicated Customer Care", "Effective Formula", "Bioavailable Formula",
        ],
    },
}


NOTES = {
    "B00JFF48I6": "Non-GMO Project Verified retained from input image claim; extracted text/specs confirm Non-GMO but not the Project Verified wording. Browser showed See all product specifications visible but disabled; saved HTML contained product specifications text.",
    "B0BT1QB131": "Excluded one unrelated About-this-item sentence referencing a Lion's Mane supplement. Product specifications did not list a Primary Supplement Type, so nutrition claims come from title/bullets.",
    "B088YG3YRL": "Brain/Cognitive Health Support, Cellular Health Support, Tasteless Formula, Easy to Swallow, and Vegetarian-Friendly were retained from the input image extraction; extracted text/specs did not clearly repeat all of that wording.",
    "B086D3TN83": "Input row had a navigation timeout, but the saved Amazon page fetched successfully. A+ comparison text mentioning Gluten-Free was not counted because product association was unclear.",
    "B086GK9SWD": "Used product-specific A+ text up to the related-products comparison. Related-product comparison rows were not counted.",
    "B07K8QLGHN": "Muscle Recovery Support and Youthful Complexion Support were retained from the input image extraction and aligned with page benefit/spec wording where possible.",
    "B07DH1ZJZ9": "No Sugar/No Junk was retained from the input image extraction; extracted text/specs did not clearly repeat it.",
    "B07DR13XSX": "Directions mention a scoop despite the capsule title; that inconsistency was not counted as a claim. Made-in-USA appeared only in a related-product comparison area and was not counted.",
    "B0F4XPWTMR": "ISO, Dye-Free, Laboratory Quality Control, and Bioavailable Formula were retained from input image extraction; text/specs confirmed several related quality and bioavailability claims but did not repeat all image-only wording.",
}


PATTERNS = {
    "Immune Support": [r"immune", r"immunity", r"defenses"],
    "Common Illness Defense": [r"common illnesses", r"colds"],
    "White Blood Cell Support": [r"white blood cells", r"antibodies"],
    "Antioxidant Support": [r"antioxidant", r"free radical"],
    "Enhanced Absorption": [r"absorption", r"absorbed", r"absorb"],
    "Fast Absorption": [r"fast absorption"],
    "Enhanced Bioavailability": [r"bioavailability", r"nutrient availability", r"bioavailable"],
    "Digestive Comfort": [r"digest", r"gastrointestinal", r"stomach", r"gentle on"],
    "General Wellness Support": [r"general wellness", r"everyday vitality", r"daily routine"],
    "Overall Well-Being Support": [r"overall well", r"overall health", r"optimal health"],
    "Cellular Health Support": [r"cellular health"],
    "Cellular Defense": [r"cellular defense"],
    "Cellular Vitality": [r"cellular vitality"],
    "Collagen Production Support": [r"collagen"],
    "Skin Health Support": [r"skin"],
    "Youthful Complexion Support": [r"youthful complexion"],
    "Joint Support": [r"joint"],
    "Joint/Connective Tissue Support": [r"connective tissue", r"joints"],
    "Cartilage/Tendon/Ligament Support": [r"cartilage", r"tendons", r"ligaments"],
    "Bone Health Support": [r"bone"],
    "Bone Density Support": [r"bone density"],
    "Teeth/Gum Health Support": [r"teeth", r"gums"],
    "Gum Health Support": [r"gum"],
    "Brain/Cognitive Health Support": [r"brain", r"cognitive", r"cognition"],
    "Mental Acuity Support": [r"mental acuity"],
    "Nerve Support": [r"nerve"],
    "Heart/Cardiovascular Support": [r"heart", r"cardiovascular"],
    "Eye Support": [r"eye"],
    "Blood Circulation Support": [r"blood circulation", r"circulation"],
    "Blood Pressure Control": [r"blood pressure"],
    "Respiratory Support": [r"respiratory", r"lungs"],
    "Calcium Absorption Support": [r"calcium"],
    "Iron Absorption Support": [r"iron"],
    "Folic Acid Utilization Support": [r"folic acid"],
    "Mood Support": [r"mood"],
    "Energy Support": [r"energy", r"fatigue"],
    "Muscle Recovery Support": [r"muscle recovery"],
    "Recovery Support": [r"recovery"],
    "Vitality Support": [r"vitality", r"vibrant", r"feeling stronger"],
    "Balanced Nutrition Support": [r"balanced nutrition"],
    "Anti-Aging Support": [r"anti-aging", r"age faster"],
    "Wrinkle Support": [r"wrinkle"],
    "Deficiency Protection": [r"deficien"],
    "Daily Wellness Support": [r"daily wellness"],
    "Resilience Support": [r"resilience"],
    "Non-GMO Project Verified": [r"non-gmo project"],
    "Non-GMO": [r"non-gmo", r"no gmos", r"without gmos", r"free of gmo", r"free from gmo"],
    "Gluten-Free": [r"gluten"],
    "Soy-Free": [r"soy"],
    "Dairy-Free": [r"dairy"],
    "Sugar-Free": [r"sugar"],
    "Preservative-Free": [r"preservative"],
    "Dye-Free": [r"dye"],
    "No Artificial Ingredients": [r"artificial ingredients"],
    "No Artificial Flavors": [r"artificial flavors"],
    "No Toxic Additives": [r"toxic additives"],
    "No Fillers": [r"fillers", r"rice flour", r"magnesium stearate"],
    "Free From Additives": [r"additives"],
    "No Animal Byproducts": [r"animal byproducts"],
    "No Eggs": [r"eggs"],
    "No Gelatin": [r"gelatin"],
    "No Caffeine": [r"caffeine"],
    "No Hormones": [r"hormones?"],
    "Vegan": [r"vegan"],
    "Vegetarian": [r"vegetarian"],
    "Vegetarian-Friendly": [r"vegetarian friendly", r"vegetarian-friendly"],
    "Plant-Based": [r"plant based", r"plant-based"],
    "Keto": [r"keto"],
    "Halal": [r"halal"],
    "Organic Ingredients": [r"organic"],
    "100% Natural": [r"100% natural"],
    "Made in USA": [r"made in the usa", r"made in usa", r"manufactured.*united states", r"manufactured.*u\\.s\\."],
    "US Manufacturing Facility": [r"us manufacturing facility", r"u\\.s\\. manufacturing"],
    "Globally Sourced Ingredients": [r"globally sourced"],
    "GMP-Certified/Compliant Facility": [r"gmp", r"cgmp"],
    "USP Good Manufacturing Practices": [r"usp good manufacturing"],
    "NSF-Approved": [r"nsf"],
    "ISO": [r"iso"],
    "Third-Party/Lab Tested": [r"third-party", r"third party", r"lab tested", r"laboratory tested"],
    "Independently Verified": [r"independently verified"],
    "Heavy Metal Tested": [r"heavy metals?"],
    "Laboratory Quality Control": [r"laboratory quality control"],
    "Quality/Purity Tested": [r"purity", r"active ingredients", r"quality"],
    "Strict Quality Standards": [r"strict quality", r"quality control"],
    "Premium Quality Ingredients": [r"premium quality"],
    "Small Business": [r"small business"],
    "Vitamin C": [r"vitamin c"],
    "Liposomal Vitamin C": [r"liposomal vitamin c"],
    "LipoQuil-C": [r"lipoquil"],
    "Fat-Soluble Vitamin C": [r"fat-soluble", r"fat soluble"],
    "Buffered Vitamin C": [r"buffered"],
    "High Dose/High Potency Vitamin C": [r"high dose", r"high potency", r"maximum potency"],
    "Vitamin C 1,000 mg per serving": [r"1,000 mg", r"1000mg", r"1000 mg"],
    "Vitamin C 1,500 mg per serving": [r"1,500 mg", r"1500mg", r"1500 mg"],
    "Vitamin C 1,650 mg": [r"1650mg", r"1,650"],
    "Vitamin C 1,700 mg per serving": [r"1700mg", r"1700 mg"],
    "Liposomal Vitamin C 1,400 mg": [r"1400mg", r"1,400"],
    "Liposomal Vitamin C 1,450 mg": [r"1450 mg"],
    "Over 1,000 mg Vitamin C": [r"over 1000 mg", r"over 1,000"],
    "Liposomal Complex 400 mg": [r"complex 400mg", r"complex 400 mg"],
    "Sunflower Oil and Lecithin Phospholipids 50 mg": [r"50mg of sunflower oil", r"50 mg of sunflower oil"],
    "Ascorbic Acid": [r"ascorbic acid"],
    "Ascorbyl Palmitate": [r"ascorbyl palmitate"],
    "Ascorbyl Oleate": [r"ascorbyl oleate"],
    "Calcium Ascorbate": [r"calcium ascorbate"],
    "Sodium Ascorbate": [r"sodium ascorbate"],
    "Cetyl Ascorbate": [r"cetyl ascorbate"],
    "Palmitic Acid": [r"palmitic acid"],
    "Organic Acerola Cherry": [r"acerola"],
    "Organic Camu Camu": [r"camu camu"],
    "Whole Food Vitamin C": [r"whole food vitamin c"],
    "Sunflower Lecithin": [r"sunflower lecithin"],
    "Sunflower Oil": [r"sunflower oil"],
    "Phospholipid": [r"phospholipid"],
    "Phospholipid Complex": [r"phospholipid complex"],
    "Phosphatidylcholine": [r"phosphatidylcholine"],
    "Dry Liposomal Complex": [r"dry liposomal"],
    "Coconut Oil/MCT": [r"coconut", r"mct"],
    "Medium Chain Triglycerides": [r"medium chain triglycerides"],
    "Capsule Form": [r"capsule"],
    "Vegetable Capsules": [r"vegetable capsules", r"vegetable capsule", r"veggie capsules"],
    "Vegan Capsules": [r"vegan capsules"],
    "2-Capsule Serving": [r"two \\(2\\) capsules", r"2 capsules"],
    "Dietary Supplement": [r"dietary supplement"],
    "Unflavored": [r"unflavored"],
    "Orange Flavor": [r"orange"],
    "120 Capsules": [r"120 capsules", r"120 count"],
    "180 Capsules": [r"180 capsules", r"180 count"],
    "200 Capsules": [r"200 capsules", r"200 count"],
    "90 Servings": [r"90 servings"],
    "100-Day Supply": [r"100-day", r"100 day"],
    "Easy to Swallow": [r"easy-to-swallow", r"easy to swallow"],
    "Easy to Take": [r"easy-to-take", r"easy to take"],
    "Taste-Friendly": [r"taste-friendly", r"taste friendly"],
    "Tasteless Formula": [r"tasteless formula"],
    "No Bad Taste": [r"no bad taste", r"bad taste"],
    "No Strong Aftertaste": [r"no strong aftertaste", r"aftertaste"],
    "No Smell": [r"no smell"],
    "No Refrigeration Needed": [r"refrigeration"],
    "Shelf-Stable": [r"go bad easily"],
    "Long Shelf Life": [r"long shelf"],
    "3-Month Supply": [r"3-month", r"3 month"],
    "90-Day Supply": [r"90 days", r"90-day"],
    "Clean Label/Purity": [r"clean label", r"purity"],
    "Premium/Pure Ingredients": [r"premium", r"pure ingredients", r"finest ingredients"],
    "Pure and Safe Ingredients": [r"pure and safe"],
    "No Unnecessary Fillers or Allergens": [r"unnecessary fillers", r"allergens"],
    "No Rice Flour": [r"rice flour"],
    "No Magnesium Stearate": [r"magnesium stearate"],
    "Strict Quality Control": [r"strict quality control", r"quality control"],
    "Batch Tested": [r"batch"],
    "Doctor-Formulated": [r"doctor-formulated"],
    "Doctor-Recommended": [r"doctor-recommended"],
    "Satisfaction Guarantee": [r"satisfaction guarantee", r"refund"],
    "Trustworthy Service": [r"trustworthy service"],
    "Dedicated Customer Care": [r"customer care"],
    "Effective Formula": [r"effective"],
    "Bioavailable Formula": [r"bioavailable formula"],
    "Affordable Compared to Liquid Form": [r"affordable"],
    "Convenient Capsules": [r"convenience"],
    "Transparency/List Every Ingredient": [r"list every"],
    "Capsule Color/Scent May Vary": [r"color and scent", r"capsule color"],
    "Allergen Warning: Contains Tree Nuts/Coconuts": [r"allergen warning", r"coconuts", r"treenuts"],
    "No Sugar/No Junk": [r"no sugar", r"no junk"],
}


APLUS_CROP_MARKERS = {
    "B086D3TN83": ["BEST SELLERS"],
    "B086GK9SWD": ["Digestive Enzymes 1000 MG"],
    "B07DR13XSX": ["DACHA Turmeric"],
}


def clean_text(text: str) -> str:
    text = (text or "").replace("\xa0", " ")
    text = text.replace("â€Ž", "").replace("â€", "")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_lines(text: str) -> list[str]:
    text = clean_text(text)
    rough = re.split(r"[\n;|]+", text)
    lines = []
    for line in rough:
        line = clean_text(line)
        if not line:
            continue
        if re.search(r"FDA|not intended to diagnose|customer reviews|buying options|price availability", line, re.I):
            continue
        lines.append(line)
    return lines


def crop_aplus(asin: str, text: str) -> str:
    for marker in APLUS_CROP_MARKERS.get(asin, []):
        idx = text.find(marker)
        if idx >= 0:
            return text[:idx]
    return text


def spec_lines(context: str) -> list[str]:
    labels = {
        "Brand Name", "Item Form", "Primary Supplement Type", "Diet Type", "Flavor",
        "Product Benefits", "Age Range Description", "Specific Uses For Product",
        "Special Ingredients", "Supplement Formulation", "Dose Release Method",
        "Manufacturer", "Unit Count", "Item Weight",
    }
    raw = [clean_text(x) for x in context.splitlines() if clean_text(x)]
    out = []
    for i, line in enumerate(raw[:-1]):
        if line in labels:
            out.append(f"Product specifications: {line} = {raw[i + 1]}")
    if "Small Business" in raw:
        out.append("Product specifications: Additional Details = Small Business")
    return out


def source_lines(asin: str, row: dict, sections: dict) -> list[tuple[str, str]]:
    lines = []
    input_claims = {
        "input image health": row.get("health_benefit_claims", ""),
        "input image certification": row.get("certification_claims", ""),
        "input image nutritional": row.get("nutritional_claims", ""),
        "input image other": row.get("other_claims", ""),
    }
    for name, label in [
        ("product_title", "Title"),
        ("feature_bullets", "About this item"),
        ("important_information", "Important information"),
    ]:
        for text in sections.get(name, []) or []:
            for line in split_lines(text):
                lines.append((label, line))

    context = sections.get("see_all_product_specifications_context") or ""
    for line in spec_lines(context):
        lines.append(("Product specifications", line))

    for text in sections.get("aplus", []) or []:
        text = crop_aplus(asin, text)
        for line in split_lines(text):
            lines.append(("A+ product description", line))
    for label, value in input_claims.items():
        if value:
            lines.append((label, value))
    return lines


def first_evidence(asin: str, claim: str, sources: list[tuple[str, str]]) -> tuple[str, str]:
    patterns = PATTERNS.get(claim, [re.escape(claim)])
    for source, line in sources:
        for pat in patterns:
            if re.search(pat, line, re.I):
                compact = clean_text(line)
                if len(compact) > 180:
                    compact = compact[:177].rstrip() + "..."
                return source, compact
    return "manual review", "Claim retained from input/product-page review; no short matching snippet was isolated automatically."


def sort_claims(category: str, claims: list[str]) -> list[str]:
    order = {claim: i for i, claim in enumerate(CLAIM_ORDER[category])}
    return sorted(dict.fromkeys(claims), key=lambda c: order.get(c, 9999))


def main() -> None:
    input_rows = {row["asin"]: row for row in csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline=""))}
    section_records = {r["asin"]: r for r in json.loads(SECTIONS_JSON.read_text(encoding="utf-8"))}

    claim_rows = []
    asin_rows = []
    for asin, categories in CLAIMS.items():
        row = input_rows[asin]
        section_record = section_records[asin]
        sources = source_lines(asin, row, section_record["sections"])
        per_category = {}
        evidence_by_category = {}

        for category in CATEGORY_ORDER:
            claims = sort_claims(category, categories.get(category, []))
            per_category[category] = claims
            evidence_items = []
            for index, claim in enumerate(claims, 1):
                source, evidence = first_evidence(asin, claim, sources)
                evidence_text = f"{claim} [{source}: {evidence}]"
                evidence_items.append(evidence_text)
                claim_rows.append({
                    "asin": asin,
                    "url": row["url"],
                    "claim_order": index,
                    "category": category,
                    "claim": claim,
                    "evidence_source": source,
                    "evidence": evidence,
                    "notes": NOTES.get(asin, ""),
                })
            evidence_by_category[category] = " || ".join(evidence_items)

        asin_rows.append({
            "asin": asin,
            "url": row["url"],
            "title": section_record["sections"].get("product_title", [row.get("title", "")])[0],
            "Health/Benefit Claims": " | ".join(per_category["Health/Benefit Claims"]),
            "Health/Benefit Claims Evidence": evidence_by_category["Health/Benefit Claims"],
            "Certification Claims": " | ".join(per_category["Certification Claims"]),
            "Certification Claims Evidence": evidence_by_category["Certification Claims"],
            "Nutritional Claims": " | ".join(per_category["Nutritional Claims"]),
            "Nutritional Claims Evidence": evidence_by_category["Nutritional Claims"],
            "Other Claims": " | ".join(per_category["Other Claims"]),
            "Other Claims Evidence": evidence_by_category["Other Claims"],
            "missed_or_unclear": NOTES.get(asin, ""),
        })

    asin_fields = [
        "asin", "url", "title",
        "Health/Benefit Claims", "Health/Benefit Claims Evidence",
        "Certification Claims", "Certification Claims Evidence",
        "Nutritional Claims", "Nutritional Claims Evidence",
        "Other Claims", "Other Claims Evidence", "missed_or_unclear",
    ]
    claim_fields = [
        "asin", "url", "claim_order", "category", "claim",
        "evidence_source", "evidence", "notes",
    ]

    with OUT_ASIN.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=asin_fields)
        writer.writeheader()
        writer.writerows(asin_rows)

    with OUT_CLAIMS.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=claim_fields)
        writer.writeheader()
        writer.writerows(claim_rows)

    with OUT_ORDER.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "claim_order", "claim"])
        writer.writeheader()
        for category in CATEGORY_ORDER:
            for index, claim in enumerate(CLAIM_ORDER[category], 1):
                writer.writerow({"category": category, "claim_order": index, "claim": claim})


if __name__ == "__main__":
    main()
