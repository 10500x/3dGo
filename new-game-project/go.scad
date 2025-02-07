
$fn=50;
module 2d_profile() {
	scale(.7)
	difference() {
		minkowski() {	
			circle(1.5, center=true);
			difference() {
			scale([1,0.3,1])
				circle(9, center=true);
			translate([0,-11,0])
				square(20, center=true);
			}
		}
	translate([-10,0,0])
	square(20, center=true);
	}
}

rotate_extrude(convexity = 10)
2d_profile();
