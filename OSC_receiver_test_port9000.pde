import oscP5.*;
import netP5.*;

OscP5 oscP5;

void setup() {
  size(400, 400);
  oscP5 = new OscP5(this, "127.0.0.1", 9000, 1);
  println("Listening on port 9000...");
}

void draw() {
  background(255);
}

void oscEvent(OscMessage theOscMessage) {
  if (theOscMessage.checkAddrPattern("/features/body") == true) {
    float arm_spread  = theOscMessage.get(0).floatValue();
    float tilt        = theOscMessage.get(1).floatValue();
    float head_height = theOscMessage.get(2).floatValue();
    float arm_elev    = theOscMessage.get(3).floatValue();
    println("arm_spread=" + arm_spread + "  tilt=" + tilt +
            "  head_height=" + head_height + "  arm_elev=" + arm_elev);
  }
}
