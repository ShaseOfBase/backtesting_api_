import vectorbtpro as vbt

default_cv_split = vbt.cv_split(
    splitter="from_n_rolling",
    splitter_kwargs=dict(n=3, split=0.5, set_labels=['train', 'test']),
    takeable_args=["data"],
    merge_func="concat",
)


def get_default_splitter(index):
    return vbt.Splitter.from_n_rolling(index=index, n=3, split=0.5, set_labels=['train', 'test'])

