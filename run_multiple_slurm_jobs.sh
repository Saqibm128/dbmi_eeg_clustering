#!/usr/bin/env bash
#
# for num_conv_spatial_layers in 1 3 5
# do
#     for num_conv_temporal_layers in 1 3 5
#     do
#       for conv_spatial_filter in "conv_spatial_filter_2_2" "conv_spatial_filter_3_3"
#       do
#           for conv_temporal_filter in "conv_temporal_filter_1_7" "conv_temporal_filter_2_3"
#             do
#               for num_spatial_filter in 100 200 300
#               do
#                 sbatch -n 1 --mem-per-cpu 16G -t 4:00:00 -p gpu --gres=gpu:1 run.sh model_name=$(hexdump -n 16 -e '4/4 "%08X" 1 "\n"' /dev/urandom).h5 n_process=1 batch_size=32 lr=0.00005 use_vp=False num_conv_spatial_layers=$num_conv_spatial_layers num_conv_temporal_layers=$num_conv_temporal_layers $conv_spatial_filter num_spatial_filter=$num_spatial_filter $conv_temporal_filter
#               done
#         done
#       done
#     done
# done
#
# #
# for num_conv_spatial_layers in 7
# do
#     for num_conv_temporal_layers in 7
#     do
#       for conv_spatial_filter in "conv_spatial_filter_2_2" "conv_spatial_filter_3_3"
#       do
#           for conv_temporal_filter in "conv_temporal_filter_1_7" "conv_temporal_filter_2_3"
#             do
#               for num_spatial_filter in 200
#               do
#                 sbatch -n 1 --mem-per-cpu 16G -t 4:00:00 -p gpu --gres=gpu:1 run.sh model_name=$(hexdump -n 16 -e '4/4 "%08X" 1 "\n"' /dev/urandom).h5  batch_size=32 n_process=1 lr=0.00005 use_vp=False num_conv_spatial_layers=$num_conv_spatial_layers patience=5 num_epochs=50 num_conv_temporal_layers=$num_conv_temporal_layers $conv_spatial_filter num_spatial_filter=$num_spatial_filter  $conv_temporal_filter
#               done
#         done
#       done
#     done
# done

# for num_conv_spatial_layers in 0 1
# do
#   for num_conv_temporal_layers in 0 1
#   do
#     for num_spatial_filter in 1 2 3 4 5 7 10
#     do
#       sbatch -n 1 --mem-per-cpu 16G -t 4:00:00 -p gpu --gres=gpu:1 run.sh standardized_combined_simple_ensemble run_on_training_loss batch_size=32 n_process=1 lr=0.0002 use_vp=False num_conv_spatial_layers=$num_conv_spatial_layers patience=5 num_conv_temporal_layers=$num_conv_temporal_layers $conv_spatial_filter  num_temporal_filter=1 num_temporal_filter=1 num_epochs=50 num_spatial_filter=$num_spatial_filter
#     done
#   done
# done


# for num_conv_spatial_layers in 0 1
# do
#   for num_conv_temporal_layers in 0 1
#   do
#     for num_spatial_filter in 1 2 3 4 5 7 10
#     do
#       for num_steps_per_epoch in 1 3 5 10 20 30 50 100
#       do
#       sbatch -n 1 --mem-per-cpu 16G -t 1:00:00 -p gpu --gres=gpu:1 run.sh steps_per_epoch=$num_steps_per_epoch standardized_combined_simple_ensemble batch_size=32 n_process=1 lr=0.0002 use_vp=False num_conv_spatial_layers=$num_conv_spatial_layers num_conv_temporal_layers=$num_conv_temporal_layers $conv_spatial_filter num_temporal_filter=1 num_spatial_filter=$num_spatial_filter
#     done
#   done
#   done
# done

# for num_conv_spatial_layers in 1 2 3
# do
#   for num_conv_temporal_layers in 1
#   do
#     for num_spatial_filter in 20 40 60 100
#     do
#       for num_steps_per_epoch in 30 50 100
#       do
#         for dropout in 0.25 0.4 0.5 0.6
#         do
#       sbatch -n 1 --mem-per-cpu 32G -t 6:00:00 -p gpu --gres=gpu:1 run.sh stop_on_training_loss steps_per_epoch=$num_steps_per_epoch standardized_combined_simple_ensemble n_process=1 lr=0.002 use_vp=False num_conv_spatial_layers=$num_conv_spatial_layers num_conv_temporal_layers=$num_conv_temporal_layers num_temporal_filter=1 num_epochs=1000 shuffle_generator=False num_spatial_filter=$num_spatial_filter dropout=$dropout
#     done
#     done
#   done
#   done
# done


# for num_conv_spatial_layers in 1 2 3
# do
#   for num_conv_temporal_layers in 1
#   do
#     for num_spatial_filter in 20 40 60 100
#     do
#       for num_steps_per_epoch in 30 50 100
#       do
#         for dropout in 0.25 0.4 0.5 0.6
#         do
#       sbatch -n 1 --mem-per-cpu 32G -t 6:00:00 -p gpu --gres=gpu:1 run.sh patience=50 stop_on_training_loss steps_per_epoch=$num_steps_per_epoch standardized_combined_simple_ensemble n_process=1 lr=0.002 use_vp=False num_conv_spatial_layers=$num_conv_spatial_layers num_conv_temporal_layers=$num_conv_temporal_layers num_temporal_filter=1 num_epochs=1000 shuffle_generator=False num_spatial_filter=$num_spatial_filter dropout=$dropout
#     done
#     done
#   done
#   done
# done
# sbatch -n 1 --mem-per-cpu 24G -t 6:00:00 -p gpu --gres=gpu:1 run.sh

# for num_conv_spatial_layers in 2 3 4
# do
#   for num_conv_temporal_layers in 2 3 4
#   do
#     for num_spatial_filter in 32 64
#     do
#       for num_steps_per_epoch in 32 64 128
#       do
#         for dropout in  0.5 0.6 0.7 0.8
#         do
#            sbatch -n 1 --mem-per-cpu 32G -t 6:00:00 -p gpu --gres=gpu:1 run.sh predictSeizureConvExp.py with batch_size=64 steps_per_epoch=$num_steps_per_epoch standardized_ensemble n_process=1 lr=0.002 use_vp=False num_conv_spatial_layers=$num_conv_spatial_layers num_conv_temporal_layers=$num_conv_temporal_layers num_temporal_filter=1 num_epochs=500 stop_on_training_loss num_spatial_filter=$num_spatial_filter use_early_stopping=True patience=75 dropout=$dropout num_epochs=500 patience=30
#            # sbatch -n 1 --mem-per-cpu 32G -t 6:00:00 -p gpu --gres=gpu:1 run.sh predictAgeConvExp.py     with batch_size=64 steps_per_epoch=$num_steps_per_epoch standardized_ensemble n_process=1 lr=0.002 use_vp=False num_conv_spatial_layers=$num_conv_spatial_layers num_conv_temporal_layers=$num_conv_temporal_layers num_temporal_filter=1 num_epochs=500 stop_on_training_loss num_spatial_filter=$num_spatial_filter use_early_stopping=True patience=75 dropout=$dropout num_epochs=500 patience=30
#   done
#     done
#   done
#   done
# done
#
# sbatch -n 1 --mem-per-cpu 32G -t 6:00:00 -p gpu --gres=gpu:4 run.sh predictSeizureConvExp.py with batch_size=64 standardized_ensemble n_process=1 lr=0.002 use_vp=False num_temporal_filter=1 num_epochs=500 num_spatial_filter=100 use_early_stopping=True patience=75 dropout=0.25 num_epochs=500 patience=10 use_dl=False use_inception_like=True num_gpus=4 use_vp=True

# for num_conv_spatial_layers in 3 4
# do
#   for num_spatial_filter in 25 50 100
#   do
#     for num_steps_per_epoch in 60
#     do
#       for dropout in 0.6 0.7
#       do
#         sbatch -n 1 --mem-per-cpu 32G -t 6:00:00 -p gpu --gres=gpu:4 run.sh predictSeizureConvExp.py with batch_size=64 steps_per_epoch=$num_steps_per_epoch standardized_ensemble n_process=1 lr=0.002 use_vp=False num_conv_spatial_layers=$num_conv_spatial_layers num_conv_temporal_layers=1 num_temporal_filter=1 num_epochs=500 stop_on_training_loss num_spatial_filter=$num_spatial_filter use_early_stopping=True patience=75 dropout=$dropout num_epochs=500 patience=03 use_dl=False use_inception_like=True num_gpus=4
#         # sbatch -n 1 --mem-per-cpu 32G -t 6:00:00 -p gpu --gres=gpu:4 run.sh predictAgeConvExp.py with batch_size=64 steps_per_epoch=$num_steps_per_epoch standardized_ensemble n_process=1 lr=0.002 use_vp=False num_conv_spatial_layers=$num_conv_spatial_layers num_conv_temporal_layers=$num_conv_temporal_layers num_temporal_filter=1 num_epochs=500 stop_on_training_loss num_spatial_filter=$num_spatial_filter use_early_stopping=True patience=75 dropout=$dropout num_epochs=500 patience=03 use_dl=False use_inception_like=True num_gpus=4
#       done
#     done
#   done
# done

# for patient_weight in 0 0.01 0.1 0.25 0.5 0.9 1 1.1 2 4 10 100
# do
#   sbatch -n 1 --mem-per-cpu 64G -t 3:00:00 -p gpu --gres=gpu:2 runPython.sh predictGenderPatientConvExp.py with batch_size=64 standardized_combined_simple_ensemble lr=0.002 num_epochs=50 patience=5 dropout=0.5 patience=5 patient_weight=$patient_weight gender_weight=1 num_gpus=2 num_filters=20
# done



for patient_weight in 1 0 -1
do
  for use_lstm in True False
    do
      for include_seizure_type in True False
      do
      sbatch -p gpu --gres=gpu:1 --dependency=afterok:60213159 -c 1 --mem-per-cpu 64G -t 4:00:00 runPython.sh predictSeizureMultipleLabels.py with second_set_params.json patient_weight=$patient_weight seizure_weight=5 lr=0.05 lr_decay=0.75 patience=5 num_filters=1 num_temporal_filter=1 num_conv_temporal_layers=3 num_layers=3 use_lstm=$use_lstm epochs=300 include_seizure_type=$include_seizure_type
    done
done
done


for patient_weight in 1 0 -1
do
  for use_lstm in True False
    do
      for include_seizure_type in True False
      do
      sbatch -p gpu --gres=gpu:1 --dependency=afterok:60213159 -c 1 --mem-per-cpu 64G -t 4:00:00 runPython.sh predictSeizureMultipleLabels.py with second_set_params.json patient_weight=$patient_weight seizure_weight=5 lr=0.05 lr_decay=0.75 patience=5 num_filters=4 num_temporal_filter=2 num_conv_temporal_layers=3 num_layers=3 use_lstm=$use_lstm epochs=300 include_seizure_type=$include_seizure_type num_post_cnn_layers=2 linear_dropout=0.5
    done
done
done
