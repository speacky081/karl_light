import enum
from typing import List

class StrAlignType(enum.Enum): LEFT, CENTER, RIGHT = range(3)

def fill_strings_to_same_length(strings:List[str], align_type:StrAlignType = StrAlignType.LEFT, left_margin:int = 0, right_margin:int = 0) -> List[str]:
    '''
    Takes all strings in a list and adds spaces, so that they are all the same length.

        Parameters:
            strings      : List of the strings to fill
            align_type   : StrAlignType.LEFT .RIGHT or .CENTER, depending on where in the result the original string is put
            left_margin  : The additional amount of spaces on the left
            right_margin : The additional amount of spaces on the right

        Returns:
            result       : List of strings that are all the same length
    '''
    if len(strings)==0:
        return strings   
    
    max_len = max(map(len, strings))

    margin_str_left = ' '*left_margin
    margin_str_right = ' '*right_margin
    result = []

    for s in strings:
        s_len = len(s)

        spaces = max_len - s_len
        if align_type == StrAlignType.LEFT:
            r = f'{s}{" "*spaces}'
        elif align_type == StrAlignType.RIGHT:
            r = f'{" "*spaces}{s}'
        else:
            r = f'{" "*(spaces//2)}{s}{" "*(spaces//2 + spaces%2)}'

        r = f'{margin_str_left}{r}{margin_str_right}'
        result.append(r)

    return result
