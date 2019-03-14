from keras.layers import *
from keras.models import *
import keras.backend as K

class Mention_Embedding(object):

    def __init__(self, filters=280, embed_size=300):
        self.filters = filters
        self.embed_size = embed_size

    def build(self):
        P_Fea1 = Input(shape=(3, self.embed_size))  # Embedding of Parents, Mention, and Suceeding Word: String Features
        P_Fea2 = Input(shape=(6, self.embed_size))  # Embeddings of 3 proceedings words, 3 succedings words of m
        P_Fea3 = Input(shape=(3, self.embed_size))
        Antecedent_Fea1 = Input(shape=(3, self.embed_size))
        Antecedent_Fea2 = Input(shape=(6, self.embed_size))
        Antecedent_Fea3 = Input(shape=(3, self.embed_size))
        Dist_Fea = Input(shape=(2,))

        Mention_Represent1 = self.mention_embed(P_Fea1, P_Fea2, P_Fea3, 'Mention')
        Mention_Represent2 = self.mention_embed(Antecedent_Fea1, Antecedent_Fea2, Antecedent_Fea3, 'Antecedent')

        x = self.mentionpair_embed(Mention_Represent1, Mention_Represent2)
        x = Concatenate(name='Mention_Pair_Embedding')([x, Dist_Fea])

        model = Model([P_Fea1, P_Fea2, P_Fea3, Antecedent_Fea1, Antecedent_Fea2, Antecedent_Fea3, Dist_Fea], x)

        return model

    def mention_embed(self, inp1, inp2, inp3, target):
        Conv1_fea1 = self.Conv1k(inp1, [1, 2, 3])
        Conv1_fea2 = self.Conv1k(inp2, [1, 2, 3])
        Conv1_fea3 = self.Conv1k(inp3, [1, 2, 3])

        self.Expand_dim = Lambda(lambda x: K.expand_dims(x, axis=1))
        Conv1_fea1 = self.Expand_dim(Conv1_fea1)
        Conv1_fea2 = self.Expand_dim(Conv1_fea2)
        Conv1_fea3 = self.Expand_dim(Conv1_fea3)
        Conv2_Input = Concatenate(axis=1)([Conv1_fea1, Conv1_fea2, Conv1_fea3])

        x = Conv2D(self.filters, kernel_size=(3, 3), activation='tanh')(Conv2_Input)
        x = MaxPool2D(pool_size=(1, 1))(x)
        x = Lambda(lambda x: K.squeeze(x, axis=1), name="{}_Embed".format(target))(x)

        return x

    def Conv1k(self, x, kernels):
        assert len(kernels) != 0
        convs = []
        shape = x.get_shape().as_list()
        for kernel in kernels:
            conv = Conv1D(self.filters, kernel, activation='tanh')(x)
            pool = MaxPool1D(pool_size=int(shape[1] - kernel + 1))(conv)
            pool = Dropout(0.8)(pool)
            convs.append(pool)

        convs = Concatenate(axis=1)(convs)

        return convs

    def mentionpair_embed(self, M1, M2):
        x = Concatenate(axis=1)([M1, M2])
        x = Conv1D(self.filters, kernel_size=2, activation='tanh')(x)
        x = MaxPool1D(pool_size=1)(x)
        x = Dropout(0.8)(x)
        x = Flatten()(x)

        return x


class Coreference_Classifier(object):

    def __init__(self, Mention_Pair, Mention_Embedding, filters=60, embed_size=300):
        self.filters = filters
        self.embed_size = embed_size
        self.Mention_Pair = Mention_Pair
        self.Mention_Embed = Mention_Embedding
        # self.customThresholdedReLU = customThresholdedReLU(theta=1.0, name="singleton_output")

    def build(self):
        M1 = Input(shape=(3, self.embed_size))  # Embedding of Parents, Mention, and Suceeding Word: String Features
        M2 = Input(shape=(6, self.embed_size))  # Embeddings of 3 proceedings words, 3 succedings words of m
        M3 = Input(shape=(3, self.embed_size))  # Average Embedding of 3 proceeding sentence, 1 succeding sentence, and current sentence
        A1 = Input(shape=(3, self.embed_size))
        A2 = Input(shape=(6, self.embed_size))
        A3 = Input(shape=(3, self.embed_size))
        B1 = Input(shape=(3, self.embed_size))
        B2 = Input(shape=(6, self.embed_size))
        B3 = Input(shape=(3, self.embed_size))
        Dist_M_A = Input(shape=(2,))  # Mention and Antecedent A
        Dist_M_B = Input(shape=(2,))  # Mention and Antecedent B

        self.Expand_dim = Lambda(lambda x: K.expand_dims(x, axis=1))
        Mention_Pair1 = self.Mention_Pair([M1, M2, M3, A1, A2, A3, Dist_M_A])
        Mention_Pair2 = self.Mention_Pair([M1, M2, M3, B1, B2, B3, Dist_M_B])
        Mention_embedding = self.Mention_Embed([M1, M2, M3])

        Cluster_Embedding = self.CONVs(Mention_embedding)
        M_Cluster_Embedding1 = self.CONVp(Mention_Pair1)
        M_Cluster_Embedding2 = self.CONVp(Mention_Pair2)
        # Mention_embedding = Flatten()(Mention_embedding)

        output1 = Concatenate()([M_Cluster_Embedding1, M_Cluster_Embedding2, Cluster_Embedding])
        output1 = Dense(self.filters, use_bias=True, activation='relu')(output1)
        output1 = Dense(self.filters, use_bias=True, activation='relu')(output1)
        output1 = Dense(3, use_bias=True, activation='softmax', name='cluster_output')(output1)

        pair1 = self.cluster_classifier(Mention_Pair1, "pair1")
        pair2 = self.cluster_classifier(Mention_Pair2, "pair2")
        output2 = Add(name='singleton_output')([pair1, pair2])

        model = Model([M1, M2, M3, A1, A2, A3, B1, B2, B3, Dist_M_A, Dist_M_B], [output1, output2])

        return model

    def CONVs(self, x):
        x1 = GlobalAvgPool1D()(x)
        x2 = GlobalMaxPool1D()(x)
        x1 = self.Expand_dim(x1)
        x2 = self.Expand_dim(x2)
        x = Concatenate(axis=1)([x1, x2])
        x = Conv1D(self.filters, kernel_size=2)(x)
        x = MaxPool1D(pool_size=1)(x)
        x = Flatten()(x)

        return x

    def CONVp(self, x):
        x = self.Expand_dim(x)
        x1 = GlobalAvgPool1D()(x)
        x2 = GlobalMaxPool1D()(x)
        x1 = self.Expand_dim(x1)
        x2 = self.Expand_dim(x2)
        x = Concatenate(axis=1)([x1, x2])
        x = Conv1D(self.filters, kernel_size=2)(x)
        x = MaxPool1D(pool_size=1)(x)
        x = Flatten()(x)

        return x

    def cluster_classifier(self, x, _name):
        x = Dense(self.filters, use_bias=True, activation='relu')(x)
        x = Dense(1, use_bias=True, activation='sigmoid', name='{}_output'.format(_name))(x)

        return x


Embedding_model = Mention_Embedding().build()
layer_name = 'Mention_Embed'
Mention_Pair = Model(Embedding_model.inputs, Embedding_model.output)
Mention_Embedding = Model([Embedding_model.inputs[0], Embedding_model.inputs[1], Embedding_model.inputs[2]],
                          Embedding_model.get_layer(layer_name).output)

model = Coreference_Classifier(Mention_Pair, Mention_Embedding).build()
model.summary()
model.compile(optimizer='adam',
              loss={'cluster_output':'sparse_categorical_crossentropy', 'singleton_output':'mse'},
              loss_weights={'cluster_output': 1.0, 'singleton_output': 1.0},
              metrics={'cluster_output':"sparse_categorical_accuracy"})