import cProfile, pstats, io


def profile(fn):
    def inner(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = fn(*args, **kwargs)
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(25)
        print(s.getvalue())
        return result
    return inner
