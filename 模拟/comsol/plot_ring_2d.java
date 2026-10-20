import com.comsol.model.*;
import com.comsol.model.util.*;

public class plot_ring_2d {
  public static void main(String[] args) throws Exception {
    ModelUtil.clear();
    Model model = ModelUtil.load("m",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ray_ring_2d_Model.mph");

    model.result("pg1").run();

    model.result().export().create("img1", "Image");
    model.result().export("img1").set("plotgroup", "pg1");
    model.result().export("img1").set("pngfilename",
      "C:/Users/qiann/Desktop/TJPT光栅/模拟/comsol/ring_2d.png");
    model.result().export("img1").set("size", "manualweb");
    model.result().export("img1").set("unit", "px");
    model.result().export("img1").set("height", "700");
    model.result().export("img1").set("width", "1100");
    model.result().export("img1").run();
  }
}
