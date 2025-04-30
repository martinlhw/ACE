import torch
import torch.nn as nn
from torchvision.models import mobilenet_v3_large, MobileNet_V3_Large_Weights

class PokerCardClassifier(nn.Module):
    def __init__(self, num_classes=52):
        """
        Poker card classification model based on ResNet18.
        
        Args:
            num_classes: 52
        """
        super(PokerCardClassifier, self).__init__()
        self.backbone = mobilenet_v3_large(weights=MobileNet_V3_Large_Weights.IMAGENET1K_V1)
        
        # Replace the final fully connected layer
        last_channel = self.backbone.classifier[0].in_features
        self.backbone.classifier = nn.Identity()
        
        self.pred_head = nn.Sequential(
            nn.Linear(last_channel, 256),
            nn.ReLU(),
            nn.Dropout(0.2),  # Add dropout for regularization
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x):
        features = self.backbone(x)
        return self.pred_head(features)

def create_optimizer(model, memorization_lr=0.0003):
    """
    Create an optimizer specifically tuned for memorization.
    Uses different learning rates for backbone and memorization head.
    
    Args:
        model: The model to optimize
        memorization_lr: Learning rate for memorization head
        
    Returns:
        Optimizer configured for memorization
    """
    # Higher learning rate for the memorization head
    # Lower learning rate for the backbone
    params = [
        {'params': model.backbone.parameters(), 'lr': memorization_lr / 10},
        {'params': model.pred_head.parameters(), 'lr': memorization_lr}
    ]
    
    # Use Adam with zero weight decay to allow perfect memorization
    optimizer = torch.optim.Adam(params, weight_decay=0)
    
    return optimizer