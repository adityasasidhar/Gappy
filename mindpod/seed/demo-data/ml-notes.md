# Machine Learning — Study Notes

## 1. Supervised vs Unsupervised Learning

**Supervised learning**: The model is trained on labeled examples — pairs of (input, desired output). The goal is to learn a mapping function. Examples: linear regression, logistic regression, decision trees, SVMs, neural networks.

**Unsupervised learning**: No labels. The model finds structure in unlabeled data. Examples: K-means clustering, PCA, autoencoders, GANs.

**Semi-supervised**: Small amount of labeled data + large amount of unlabeled data. Useful when labeling is expensive.

**Reinforcement learning**: An agent learns by interacting with an environment and receiving reward signals. Not covered in this course.

---

## 2. Gradient Descent

The core optimization algorithm in most ML models.

**Intuition**: Imagine a ball rolling down a hilly surface to the lowest valley. We want to find the minimum of our loss function.

**Update rule**: θ = θ − α · ∇L(θ)

Where:
- θ = model parameters (weights)
- α = learning rate (step size)
- ∇L(θ) = gradient of loss w.r.t. parameters

**Learning rate**:
- Too high → overshoots minimum → training diverges
- Too low → converges very slowly
- Typical range: 0.001 to 0.1 (use a learning rate scheduler)

**Variants**:
- Batch GD: Use all data for each update. Stable but slow.
- Stochastic GD (SGD): One example per update. Fast but noisy.
- Mini-batch GD: k examples per update (k=32–256 typical). Best of both.

---

## 3. Overfitting and Regularization

**Overfitting**: Model learns the training data too well — memorizes noise. High training accuracy, low validation accuracy.

**Underfitting**: Model is too simple to capture patterns. Low accuracy on both train and val.

**Bias-variance tradeoff**:
- High bias = underfitting
- High variance = overfitting
- Want the sweet spot

**Regularization techniques**:
- L1 (Lasso): Adds |w| penalty. Encourages sparsity.
- L2 (Ridge): Adds w² penalty. Shrinks all weights.
- Dropout: Randomly zero out neurons during training (common in deep nets)
- Early stopping: Stop training when val loss starts increasing
- Data augmentation: Generate more training examples synthetically

---

## 4. Backpropagation

The algorithm for computing gradients in neural networks. Uses the chain rule of calculus.

Given a neural network loss L = f(x; W), backprop computes ∂L/∂W for every layer.

**Chain rule**: If y = f(g(x)), then dy/dx = f'(g(x)) · g'(x)

**Forward pass**: Compute activations layer by layer.
**Backward pass**: Propagate error gradients from output to input.

⚠️ *This section is underexplained in these notes — see 3Blue1Brown "Backpropagation calculus" for intuition.*

---

## 5. Evaluation Metrics

| Task | Metric |
|------|--------|
| Binary classification | Accuracy, Precision, Recall, F1, AUC-ROC |
| Multi-class | Top-1/Top-5 accuracy, macro/micro F1 |
| Regression | MSE, MAE, R² |
| Ranking | NDCG, MAP |

**Confusion matrix**: TP, TN, FP, FN
- Precision = TP / (TP + FP) — of predicted positives, how many are correct?
- Recall = TP / (TP + FN) — of actual positives, how many did we catch?
- F1 = 2 · (P · R) / (P + R) — harmonic mean
