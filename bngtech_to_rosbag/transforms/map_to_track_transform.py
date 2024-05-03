from scipy.spatial.transform import Rotation
import sensors.msg_iface

class MapToTrackTransform:
  def __init__(self, origin, orientation):
    self.origin = origin
    self.rotation = Rotation.from_quat(orientation).inv()
    self.tf_data = sensors.msg_iface.TransformData(
      time = 0,
      frame = 'map',
      child_frame = 'track',
      translation = origin,
      rotation = orientation
    )

  def transform_vector(self, v):
    return self.rotation.apply(v)

  def transform_position(self, p):
    return self.rotation.apply(p - self.origin)

  def transform_orientation(self, quat):
    return (self.rotation * Rotation(quat)).as_quat()