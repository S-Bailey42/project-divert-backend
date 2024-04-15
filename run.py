import fire
import uvicorn
import app
from functools import partial

def test(func, *args, **kwargs):
    def ret(*ret_args, **ret_kwargs):
        return func(*(args+ret_args),**(kwargs|ret_kwargs))
    return ret
if __name__ == "__main__":
    #wow = test(print, "nice", "day", sep="@")
    
    main = partial(uvicorn.run, "app:app")
    
    fire.Fire(main)