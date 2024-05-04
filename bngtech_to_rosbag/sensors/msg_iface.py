from dataclasses import dataclass
import numpy as np

from . import msg_helpers
from . import math_helpers

def vec_cov_pair(n, m):
  def decorator(cls):
    def ground_truth(data):
      if not isinstance(data, np.ndarray):
        data = np.array(data, dtype=np.float64)

      return cls(
        data = data.reshape((n, )),
        covariance = np.zeros((m, m), dtype=np.float64)
      )
  
    def add_variance(obj, sigma):
      obj.covariance += np.eye(m) * sigma
    
    def post_init(obj):
      assert(obj.data.shape == (n,))
      assert(obj.covariance.shape == (m,m))

    cls.ground_truth = ground_truth
    cls.add_variance = add_variance
    cls.__post_init__ = post_init
    return cls
  return decorator

@dataclass
@vec_cov_pair(3, 3)
class Vector3Covariance3Pair:
  data: np.ndarray[np.float64]
  covariance: np.ndarray[np.float64]

@dataclass
@vec_cov_pair(4, 3)
class Vector4Covariance3Pair:
  data: np.ndarray[np.float64]
  covariance: np.ndarray[np.float64]

@dataclass
class ImuData:
  time: float
  frame: str
  orientation: Vector4Covariance3Pair
  angular_velocity: Vector3Covariance3Pair
  linear_acceleration: Vector3Covariance3Pair

  def to_msg(self, typestore):
    ns, stamp = msg_helpers.stamp_from_float(self.time, typestore)

    return ns, typestore.types['sensor_msgs/msg/Imu'](
      header = msg_helpers.header(typestore, self.frame, stamp),
      orientation = msg_helpers.quaternion(typestore, self.orientation.data),
      angular_velocity = msg_helpers.vector3(typestore, self.angular_velocity.data),
      linear_acceleration = msg_helpers.vector3(typestore, self.linear_acceleration.data),
      orientation_covariance = self.orientation.covariance.flatten(),
      angular_velocity_covariance = self.angular_velocity.covariance.flatten(),
      linear_acceleration_covariance = self.linear_acceleration.covariance.flatten()
    )
  
  def apply_tf(self, tf):
    # self.angular_velocity.data = tf.transform_rpy(self.angular_velocity.data)
    self.linear_acceleration.data = tf.transform_vector(self.linear_acceleration.data)
    self.orientation.data = tf.transform_orientation(self.orientation.data)

@dataclass
class PoseData:
  time: float
  frame: str
  position: Vector3Covariance3Pair
  orientation: Vector4Covariance3Pair

  def to_msg(self, typestore):
    ns, stamp = msg_helpers.stamp_from_float(self.time, typestore)
    
    return ns, msg_helpers.with_covariance(typestore, 'pose',
      msg_helpers.header(typestore, self.frame, stamp),
      math_helpers.concat_indip_covariances(self.position.covariance, self.orientation.covariance),
      typestore.types['geometry_msgs/msg/Pose'](
        position = msg_helpers.point(typestore, self.position.data),
        orientation = msg_helpers.quaternion(typestore, self.orientation.data)
      )
    )
  
  def apply_tf(self, tf):
    self.position.data = tf.transform_position(self.position.data)
    self.orientation.data = tf.transform_orientation(self.orientation.data)
  
@dataclass
class TransformData:
  time: float
  frame: str
  child_frame: str
  translation: np.ndarray[np.float64]
  rotation: np.ndarray[np.float64]

  def to_msg(self, typestore):
    ns, stamp = msg_helpers.stamp_from_float(self.time, typestore)

    return ns, typestore.types['tf2_msgs/msg/TFMessage'](
      transforms = [
        typestore.types['geometry_msgs/msg/TransformStamped'](
          header = msg_helpers.header(typestore, self.frame, stamp),
          child_frame_id = self.child_frame,
          transform = typestore.types['geometry_msgs/msg/Transform'](
            translation = msg_helpers.vector3(typestore, self.translation),
            rotation = msg_helpers.quaternion(typestore, self.rotation)
          )
        )
      ]
    )
  
  def apply_tf(self, tf):
    self.translation = tf.transform_position(self.translation)
    self.rotation = tf.transform_orientation(self.rotation)
  
@dataclass
class TwistData:
  time: float
  frame: str
  linear: Vector3Covariance3Pair
  angular: Vector3Covariance3Pair

  def to_msg(self, typestore):
    ns, stamp = msg_helpers.stamp_from_float(self.time, typestore)

    return ns, msg_helpers.with_covariance(typestore, 'twist',
      msg_helpers.header(typestore, self.frame, stamp),
      math_helpers.concat_indip_covariances(self.linear.covariance, self.angular.covariance),
      typestore.types['geometry_msgs/msg/Twist'](
        linear = msg_helpers.vector3(typestore, self.linear.data),
        angular = msg_helpers.vector3(typestore, self.angular.data)
      )
    )
  
  def apply_tf(self, tf):
    self.linear.data = tf.transform_vector(self.linear.data)
    self.angular.data = tf.transform_rpy(self.angular.data)
  
def sensors_to_msg(typestore, sensors):
  return { k: [x.to_msg(typestore) for x in data] for k, data in sensors.items() }