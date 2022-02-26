
import torch.nn as nn

from param import args
from lxrt.entry import LXRTEncoder
from lxrt.modeling import BertLayerNorm, GeLU

# Max length including <bos> and <eos>
MAX_PVQA_LENGTH = 20


class PVQAAutoencoderModel(nn.Module):
    def __init__(self, num_answers):
        super().__init__()

        # Build LXRT encoder
        # lxrt.entry.LXRTEncoder -> LXRTFeatureExtraction -> LXRTModel
        self.lxrt_encoder = LXRTEncoder(
            args,
            max_seq_length=MAX_PVQA_LENGTH
        )

#         self.encoder = nn.Sequential(
#             nn.Linear(768, 1),
#             nn.ReLU()
#         )

#         self.decoder = nn.Sequential(
#             nn.Linear(1, 768),
#             nn.ReLU()
#         )
        hid_dim = self.lxrt_encoder.dim
        
        # VQA Answer heads
        self.temp = nn.Sequential(
            nn.Linear(hid_dim, hid_dim * 2),
            GeLU()
        )
        self.logit_fc = nn.Sequential(
#             nn.Linear(hid_dim, hid_dim * 2),
#             GeLU(),
            nn.Linear(hid_dim * 2, hid_dim * 2),
            GeLU(),
            BertLayerNorm(hid_dim * 2, eps=1e-12),
            nn.Linear(hid_dim * 2, num_answers)
        )
        self.logit_fc.apply(self.lxrt_encoder.model.init_bert_weights)
        self.temp.apply(self.lxrt_encoder.model.init_bert_weights)
        
#         self.encoder.apply(self.lxrt_encoder.model.init_bert_weights)
#         self.decoder.apply(self.lxrt_encoder.model.init_bert_weights)

    def forward(self, feat, pos, sent, target_answers, t='vqa'):
        """
        b -- batch_size, o -- object_number, f -- visual_feature_size
        :param feat: (b, o, f)
        :param pos:  (b, o, 4)
        :param sent: (b,) Type -- list of string
        :param leng: (b,) Type -- int numpy array
        :return: (b, num_answer) The logit of each answers.
        """
        x = self.lxrt_encoder(
            sent, (feat, pos), target_answers, t=t)  # embedding
        # logit = self.logit_fc(x) #answer prediction
#         encoded = self.encoder(x)
#         decoded = self.decoder(encoded)
#         logit = self.logit_fc(decoded)
        x = self.temp(x)
        logit = self.logit_fc(x)
        
        return logit
