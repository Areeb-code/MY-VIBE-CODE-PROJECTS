import * as tf from '@tensorflow/tfjs';

/*
  MindForge Neural Network Service
  This class handles model creation, training, and prediction for custom drawing recognition.
*/

class NeuralNetworkService {
  constructor() {
    this.model = null;
    this.isTraining = false;
    this.labels = [];
  }

  // Create a CNN model for image classification
  createModel(numClasses) {
    const model = tf.sequential();

    // Convolutional layer
    model.add(tf.layers.conv2d({
      inputShape: [28, 28, 1],
      kernelSize: 3,
      filters: 8,
      activation: 'relu'
    }));
    model.add(tf.layers.maxPooling2d({ poolSize: [2, 2] }));

    // Flattening
    model.add(tf.layers.flatten());

    // Hidden layer
    model.add(tf.layers.dense({ units: 64, activation: 'relu' }));

    // Output layer
    model.add(tf.layers.dense({ units: numClasses, activation: 'softmax' }));

    model.compile({
      optimizer: tf.train.adam(),
      loss: 'categoricalCrossentropy',
      metrics: ['accuracy']
    });

    this.model = model;
    return model;
  }

  // Convert canvas data to tensor
  processImage(canvas) {
    return tf.tidy(() => {
      // Get image data from canvas
      const tensor = tf.browser.fromPixels(canvas, 1) // 1 channel (grayscale)
        .resizeNearestNeighbor([28, 28])
        .toFloat()
        .div(255.0)
        .expandDims(0);
      return tensor;
    });
  }

  async train(dataset, onEpochEnd) {
    if (dataset.length === 0) return;

    const uniqueLabels = [...new Set(dataset.map(d => d.label))];
    this.labels = uniqueLabels;
    const numClasses = uniqueLabels.length;

    this.createModel(numClasses);

    // Prepare data
    const xs = tf.concat(dataset.map(d => this.processImage(d.canvas)));
    
    const labelValues = dataset.map(d => uniqueLabels.indexOf(d.label));
    const ys = tf.oneHot(tf.tensor1d(labelValues, 'int32'), numClasses);

    this.isTraining = true;

    await this.model.fit(xs, ys, {
      epochs: 20,
      shuffle: true,
      callbacks: {
        onEpochEnd: (epoch, logs) => {
          onEpochEnd(epoch, logs);
        }
      }
    });

    this.isTraining = false;
    
    // Clean up
    xs.dispose();
    ys.dispose();
  }

  predict(canvas) {
    if (!this.model) return null;

    return tf.tidy(() => {
      const input = this.processImage(canvas);
      const prediction = this.model.predict(input);
      const probabilities = prediction.dataSync();
      const index = prediction.argMax(-1).dataSync()[0];
      
      return {
        label: this.labels[index],
        confidence: probabilities[index]
      };
    });
  }
}

export const neuralNetwork = new NeuralNetworkService();
