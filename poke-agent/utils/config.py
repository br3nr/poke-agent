from google.generativeai.types import HarmCategory, HarmBlockThreshold

safety_filters={
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    #HarmCategory.HARM_CATEGORY_TOXICITY: HarmBlockThreshold.BLOCK_NONE,
    #HarmCategory.HARM_CATEGORY_SEXUAL: HarmBlockThreshold.BLOCK_NONE,
    #HarmCategory.HARM_CATEGORY_VIOLENCE: HarmBlockThreshold.BLOCK_NONE,
    #HarmCategory.HARM_CATEGORY_MEDICAL: HarmBlockThreshold.BLOCK_NONE,
    #HarmCategory.HARM_CATEGORY_DANGEROUS: HarmBlockThreshold.BLOCK_NONE,
    #HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
    #HarmCategory.HARM_CATEGORY_DEROGATORY: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
}

