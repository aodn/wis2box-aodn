module "poc-imos-wis2-2a" {
  source = "./ec2"
  instance_name = "poc-imos-wis2-2a"
}

module "poc-imos-wis2-2a-test" {
  source = "./ec2"
  instance_name = "poc-imos-wis2-2a-test"
}