
class FDOptionsBase:
    ...  # typing


class FaceDetectOptions(FDOptionsBase):
    @classmethod
    def frombody(cls, body):
        return cls(
            drawOnly='box' in body['operation'],
            limit=body['maxfaces'],
            resize='resize' in body['operation'],
            pad='pad' in body['operation'],
            multiplier=body['multiplier'],
            minw=body['minwidth'],
            minh=body['minheight'])

    def __init__(self, drawOnly=False,
                 limit=5,
                 resize=True,
                 pad=True,
                 squeeze=True,
                 multiplier=1,
                 minw=0,
                 minh=0) -> None:

        self.drawOnly = drawOnly
        self.limit = limit
        self.resize = resize
        self.pad = pad
        self.squeeze = squeeze
        self.multiplier = multiplier
        self.minw = minw
        self.minh = minh


class ShrinkOptions(FDOptionsBase):
    @classmethod
    def frombody(cls, body):
        return cls(newheight=body['newheight'], newwidth=body['newwidth'])

    def __init__(self, newheight=0, newwidth=0) -> None:
        self.newheight = newheight
        self.newwidth = newwidth


class DetectRouteKeys:
    numeric_keys = set(['maxfaces', 'minheight', 'minwidth', 'multiplier'])
    alpha_keys = set(['operation', 'mimetype', 'filename'])
    base64_keys = set(['imagedata'])
    all_keys: set[str]
    required_keys: set[str]


DetectRouteKeys.all_keys = DetectRouteKeys.numeric_keys.union(DetectRouteKeys.alpha_keys).union(DetectRouteKeys.base64_keys)
DetectRouteKeys.required_keys = DetectRouteKeys.all_keys


class ShrinkRouteKeys:
    numeric_keys = set(['newheight', 'newwidth'])
    alpha_keys = set(['mimetype', 'filename'])
    base64_keys = set(['imagedata'])
    all_keys: set[str]
    required_keys: set[str]


ShrinkRouteKeys.all_keys = ShrinkRouteKeys.numeric_keys.union(ShrinkRouteKeys.alpha_keys).union(ShrinkRouteKeys.base64_keys)
ShrinkRouteKeys.required_keys = ShrinkRouteKeys.all_keys


class FileNameError(ValueError, OSError):
    pass


class InvalidImageSizeError(ValueError):
    pass
