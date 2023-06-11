import vectorbtpro as vbt

rolling_split = vbt.cv_split(
    splitter="from_rolling",
    splitter_kwargs=dict(length=3, split=0.67, set_labels=['train', 'test'], offset=0),
    takeable_args=["data"],  # Remember to adjust this if the strategy takes more than close
    merge_func="concat",
)

default_cv_split = vbt.cv_split(
    splitter="from_n_rolling",
    splitter_kwargs=dict(n=3, split=0.5, set_labels=['train', 'test']),
    takeable_args=["data"],
    merge_func="concat",
)

rdm_sub_cv_split = vbt.cv_split(
    splitter="from_n_rolling",
    splitter_kwargs=dict(n=3, split=0.5, set_labels=['train', 'test']),
    takeable_args=["data"],
    merge_func="concat",
    random_subset=15
)

std_parameterized = vbt.parameterized(merge_func="concat")
rdm_sub_parameterized = vbt.parameterized(merge_func="concat", random_subset=500)
