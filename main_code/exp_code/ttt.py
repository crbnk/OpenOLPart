def cal_delta(T, item):
    if choose_count[item] == 0:
        return 1
    else:
        return np.sqrt(2*np.log(T) / choose_count[item])

def UCB(t, N):
    upper_bound_probs = [estimated_award[item] + cal_delta(t, item) for item in range(N)]
    item = np.argmax(upper_bound_probs)
    reward = np.random.binomial(n=1, p=true_award[item])
    return item, reward


class OLLinUCB():

    def __init__(self, ndims, alpha, app_id, core_narms=9, llc_narms=55, band_namrms=10):
        self.num_app = len(app_id)
        self.app_id = app_id

        self.core_narms = core_narms
        self.llc_narms = llc_narms
        self.band_namrms = band_namrms

        # explore-exploit parameter
        self.alpha = alpha

        self.A_c = {}
        self.b_c = {}
        self.p_c_t = {}

        self.A_l = {}
        self.b_l = {}
        self.p_l_t = {}

        self.A_b = {}
        self.b_b = {}
        self.p_b_t = {}

        for i in app_id:
            self.A_c[i] = np.zeros(self.core_narms)
            self.b_c[i] = np.zeros(self.core_narms)
            self.p_c_t[i] = np.zeros(self.core_narms)

            self.A_l[i] = np.zeros(self.llc_narms)
            self.b_l[i] = np.zeros(self.llc_narms)
            self.p_l_t[i] = np.zeros(self.llc_narms)

            self.A_b[i] = np.zeros(self.band_namrms)
            self.b_b[i] = np.zeros(self.band_namrms)
            self.p_b_t[i] = np.zeros(self.band_namrms)
            for arm in range(self.core_narms):
                self.A_c[i][arm] = np.eye(self.ndims * 2)

            for arm in range(self.llc_narms):
                self.A_l[i][arm] = np.eye(self.ndims * 2)

            for arm in range(self.band_namrms):
                self.A_b[i][arm] = np.eye(self.ndims * 2)

        super().__init__()
        return

    def add_del_app(self, app_id):
        A_c, A_l, A_b = 0, 0, 0
        for i in self.A_c.keys():
            A_c += self.A_c[i]
            A_l += self.A_l[i]
            A_b += self.A_b[i]

        for i in app_id:
            if i not in self.A_c.keys():
                self.A_c[i] = np.zeros((self.core_narms, self.ndims * 2, self.ndims * 2))
                self.b_c[i] = np.zeros((self.core_narms, self.ndims * 2, 1))
                self.p_c_t[i] = np.zeros((self.core_narms))
                for arm in range(self.core_narms):
                    self.A_c[i][arm] = A_c[arm] / self.num_app

                self.A_l[i] = np.zeros((self.llc_narms, self.ndims * 2, self.ndims * 2))
                self.b_l[i] = np.zeros((self.llc_narms, self.ndims * 2, 1))
                self.p_l_t[i] = np.zeros((self.llc_narms))
                for arm in range(self.llc_narms):
                    self.A_l[i][arm] = A_l[arm] / self.num_app

                self.A_b[i] = np.zeros((self.band_namrms, self.ndims * 2, self.ndims * 2))
                self.b_b[i] = np.zeros((self.band_namrms, self.ndims * 2, 1))
                self.p_b_t[i] = np.zeros((self.band_namrms))
                for arm in range(self.band_namrms):
                    self.A_b[i][arm] = A_b[arm] / self.num_app

        self.num_app = len(app_id)
        self.app_id = app_id

    def play(self, context, other_context, times):
        assert len(context[self.app_id[0]]) == self.ndims, 'the shape of context size is wrong'
        llc_action = {}
        band_action = {}
        contexts = {}
        # gains per each arm
        # only calculate the app in this colocation
        for key in self.app_id:
            A = self.A_c[key]
            b = self.b_c[key]
            contexts[key] = np.hstack((context[key], other_context[key]))

            for i in range(self.core_narms):
                # initialize theta hat
                theta = inv(A[i]).dot(b[i])
                # get context of each arm from flattened vector of length 100
                cntx = np.array(contexts[key])
                # get gain reward of each arm
                self.p_c_t[key][i] = theta.T.dot(cntx) + self.alpha * np.sqrt(cntx.dot(inv(A[i]).dot(cntx)))

            A = self.A_l[key]
            b = self.b_l[key]
            for i in range(self.llc_narms):
                theta = inv(A[i]).dot(b[i])
                cntx = np.array(contexts[key])
                self.p_l_t[key][i] = theta.T.dot(cntx) + self.alpha * np.sqrt(cntx.dot(inv(A[i]).dot(cntx)))

            llc_action[key] = np.random.choice(np.where(self.p_l_t[key] == max(self.p_l_t[key]))[0])

            A = self.A_b[key]
            b = self.b_b[key]
            for i in range(self.band_namrms):
                theta = inv(A[i]).dot(b[i])
                cntx = np.array(contexts[key])
                self.p_b_t[key][i] = theta.T.dot(cntx) + self.alpha * np.sqrt(cntx.dot(inv(A[i]).dot(cntx)))
            band_action[key] = np.random.choice(np.where(self.p_b_t[key] == max(self.p_b_t[key]))[0])

        core_action = beam_search(self.core_narms, self.app_id, self.p_c_t, times, end_condition=30)
        return core_action, llc_action, band_action

    def update(self, core_arms, llc_arms, band_arms, reward, context, other_context):
        contexts = {}
        for key in self.app_id:
            arm = core_arms[key]

            contexts[key] = np.hstack((context[key], other_context[key]))

            self.A_c[key][arm] += np.outer(np.array(contexts[key]),
                                           np.array(contexts[key]))

            self.b_c[key][arm] = np.add(self.b_c[key][arm].T,
                                        np.array(contexts[key]) * reward).reshape(
                self.ndims * 2, 1)

            arm = llc_arms[key]
            self.A_l[key][arm] += np.outer(np.array(contexts[key]),
                                           np.array(contexts[key]))
            self.b_l[key][arm] = np.add(self.b_l[key][arm].T,
                                        np.array(contexts[key]) * reward).reshape(
                self.ndims * 2, 1)

            arm = band_arms[key]
            self.A_b[key][arm] += np.outer(np.array(contexts[key]),
                                           np.array(contexts[key]))
            self.b_b[key][arm] = np.add(self.b_b[key][arm].T,
                                        np.array(contexts[key]) * reward).reshape(
                self.ndims * 2, 1)